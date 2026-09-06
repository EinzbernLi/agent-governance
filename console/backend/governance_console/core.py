from __future__ import annotations

import asyncio
import base64
import re
from typing import Any

import httpx
from pydantic import BaseModel, Field

from .config import Settings


CLAIM_RE = re.compile(
    r"(?m)^\[GOVERNANCE-LEAD-CLAIM-G(?P<generation>\d+)(?:-[^\]]+)?\]\s*$"
)
VERIFY_RE = re.compile(
    r"(?m)^\[GOVERNANCE-LEAD-G(?P<generation>\d+)-ACTIVATION-VERIFY(?:-[^\]]+)?\]\s*$"
)
ACTIVE_STATUS_RE = re.compile(r"(?m)^\s*active_lead_status:\s*ACTIVE\s*$")
ACTIVE_CLAIM_REF_RE = re.compile(r"(?m)^\s*active_claim_ref:\s*(?P<claim>\d+)\s*$")


class RepositorySummary(BaseModel):
    repository: str
    branch: str
    commit_sha: str
    version: str


class LeadState(BaseModel):
    status: str
    generation: int | None = None
    claim_comment_id: int | None = None
    activation_comment_id: int | None = None
    conflict_comment_ids: list[int] = Field(default_factory=list)
    lead_issue: int


class IssueSummary(BaseModel):
    number: int
    title: str
    url: str
    updated_at: str | None = None
    labels: list[str] = Field(default_factory=list)


class PullRequestSummary(BaseModel):
    number: int
    title: str
    url: str
    draft: bool = False
    state: str
    head_ref: str
    head_sha: str
    base_ref: str
    updated_at: str | None = None


class DashboardSummary(BaseModel):
    authority_mode: str = "derived_read_only"
    repository: RepositorySummary
    lead: LeadState
    issues: list[IssueSummary]
    pull_requests: list[PullRequestSummary]


class GitHubClient:
    def __init__(self, settings: Settings) -> None:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "agent-governance-console/0.1",
        }
        if settings.github_token:
            headers["Authorization"] = f"Bearer {settings.github_token}"
        self._client = httpx.AsyncClient(
            base_url="https://api.github.com", headers=headers, timeout=20.0
        )
        self.repository = settings.repository

    async def close(self) -> None:
        await self._client.aclose()

    async def _get(self, path: str, *, params: dict[str, Any] | None = None) -> Any:
        response = await self._client.get(path, params=params)
        response.raise_for_status()
        return response.json()

    async def get_branch(self, branch: str) -> dict[str, Any]:
        return await self._get(f"/repos/{self.repository}/branches/{branch}")

    async def get_contents_text(self, path: str, ref: str) -> str:
        payload = await self._get(
            f"/repos/{self.repository}/contents/{path}", params={"ref": ref}
        )
        if not isinstance(payload, dict) or payload.get("encoding") != "base64":
            raise ValueError(f"GitHub contents response for {path!r} is not base64 text")
        encoded = payload.get("content")
        if not isinstance(encoded, str):
            raise ValueError(f"GitHub contents response for {path!r} has no content")
        return base64.b64decode(encoded).decode("utf-8")

    async def get_issue_comments(self, issue_number: int) -> list[dict[str, Any]]:
        return await self._paginate(
            f"/repos/{self.repository}/issues/{issue_number}/comments"
        )

    async def get_open_issues(self) -> list[dict[str, Any]]:
        items = await self._paginate(
            f"/repos/{self.repository}/issues", extra_params={"state": "open"}
        )
        return [item for item in items if "pull_request" not in item]

    async def get_open_pulls(self) -> list[dict[str, Any]]:
        return await self._paginate(
            f"/repos/{self.repository}/pulls", extra_params={"state": "open"}
        )

    async def _paginate(
        self, path: str, *, extra_params: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for page in range(1, 11):
            params = {"per_page": 100, "page": page}
            if extra_params:
                params.update(extra_params)
            payload = await self._get(path, params=params)
            if not isinstance(payload, list):
                raise ValueError(f"GitHub list response expected for {path}")
            results.extend(item for item in payload if isinstance(item, dict))
            if len(payload) < 100:
                return results
        raise ValueError(
            f"GitHub pagination exceeded 1000 items for {path}; derived state is incomplete"
        )


def parse_lead_state(
    comments: list[dict[str, Any]], *, lead_issue: int
) -> LeadState:
    claims: dict[int, list[dict[str, Any]]] = {}
    verifications: dict[int, list[dict[str, Any]]] = {}

    for comment in comments:
        body = comment.get("body")
        if not isinstance(body, str):
            continue
        claim_match = CLAIM_RE.search(body)
        if claim_match:
            generation = int(claim_match.group("generation"))
            claims.setdefault(generation, []).append(comment)
        verify_match = VERIFY_RE.search(body)
        if verify_match:
            generation = int(verify_match.group("generation"))
            verifications.setdefault(generation, []).append(comment)

    if not claims:
        return LeadState(status="unknown", lead_issue=lead_issue)

    generation = max(claims)
    latest_claims = claims[generation]
    if len(latest_claims) != 1:
        return LeadState(
            status="conflict",
            generation=generation,
            conflict_comment_ids=sorted(
                int(comment["id"])
                for comment in latest_claims
                if isinstance(comment.get("id"), int)
            ),
            lead_issue=lead_issue,
        )

    claim = latest_claims[0]
    claim_id = claim.get("id") if isinstance(claim.get("id"), int) else None
    active_verifications: list[dict[str, Any]] = []
    if claim_id is not None:
        for comment in verifications.get(generation, []):
            body = comment.get("body")
            if not isinstance(body, str) or not ACTIVE_STATUS_RE.search(body):
                continue
            claim_ref_match = ACTIVE_CLAIM_REF_RE.search(body)
            if not claim_ref_match:
                continue
            if int(claim_ref_match.group("claim")) != claim_id:
                continue
            active_verifications.append(comment)

    activation_id: int | None = None
    if active_verifications:
        chosen = max(
            active_verifications,
            key=lambda comment: int(comment.get("id", 0))
            if isinstance(comment.get("id"), int)
            else 0,
        )
        activation_id = chosen.get("id") if isinstance(chosen.get("id"), int) else None

    return LeadState(
        status="active" if activation_id is not None else "claimed_unverified",
        generation=generation,
        claim_comment_id=claim_id,
        activation_comment_id=activation_id,
        lead_issue=lead_issue,
    )


class ConsoleService:
    def __init__(self, client: GitHubClient, settings: Settings) -> None:
        self.client = client
        self.settings = settings

    async def repository_summary(self) -> RepositorySummary:
        branch = await self.client.get_branch(self.settings.branch)
        commit = branch.get("commit") if isinstance(branch, dict) else None
        sha = commit.get("sha") if isinstance(commit, dict) else None
        if not isinstance(sha, str) or not sha:
            raise ValueError("GitHub branch response did not contain a commit SHA")
        version = (await self.client.get_contents_text("VERSION", sha)).strip()
        return RepositorySummary(
            repository=self.settings.repository,
            branch=self.settings.branch,
            commit_sha=sha,
            version=version,
        )

    async def lead_state(self) -> LeadState:
        comments = await self.client.get_issue_comments(self.settings.lead_issue)
        return parse_lead_state(comments, lead_issue=self.settings.lead_issue)

    async def issues(self) -> list[IssueSummary]:
        items = await self.client.get_open_issues()
        return [
            IssueSummary(
                number=int(item["number"]),
                title=str(item.get("title", "")),
                url=str(item.get("html_url", "")),
                updated_at=item.get("updated_at")
                if isinstance(item.get("updated_at"), str)
                else None,
                labels=[
                    str(label.get("name"))
                    for label in item.get("labels", [])
                    if isinstance(label, dict) and label.get("name") is not None
                ],
            )
            for item in items
            if isinstance(item.get("number"), int)
        ]

    async def pull_requests(self) -> list[PullRequestSummary]:
        items = await self.client.get_open_pulls()
        results: list[PullRequestSummary] = []
        for item in items:
            head = item.get("head") if isinstance(item.get("head"), dict) else {}
            base = item.get("base") if isinstance(item.get("base"), dict) else {}
            if not isinstance(item.get("number"), int):
                continue
            results.append(
                PullRequestSummary(
                    number=int(item["number"]),
                    title=str(item.get("title", "")),
                    url=str(item.get("html_url", "")),
                    draft=bool(item.get("draft", False)),
                    state=str(item.get("state", "unknown")),
                    head_ref=str(head.get("ref", "")),
                    head_sha=str(head.get("sha", "")),
                    base_ref=str(base.get("ref", "")),
                    updated_at=item.get("updated_at")
                    if isinstance(item.get("updated_at"), str)
                    else None,
                )
            )
        return results

    async def dashboard(self) -> DashboardSummary:
        repository, lead, issues, pulls = await asyncio.gather(
            self.repository_summary(),
            self.lead_state(),
            self.issues(),
            self.pull_requests(),
        )
        return DashboardSummary(
            repository=repository,
            lead=lead,
            issues=issues,
            pull_requests=pulls,
        )
