from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi.testclient import TestClient

from governance_console.core import (
    DashboardSummary,
    IssueSummary,
    LeadState,
    PullRequestSummary,
    RepositorySummary,
)
from governance_console.main import app, get_service


EXAMPLE_LEAD_ISSUE = 73


class FakeService:
    async def repository_summary(self) -> RepositorySummary:
        return RepositorySummary(
            repository="example/governance",
            branch="main",
            commit_sha="abc123",
            version="9.9.9",
        )

    async def lead_state(self) -> LeadState:
        return LeadState(
            status="active",
            generation=8,
            claim_comment_id=100,
            activation_comment_id=101,
            lead_issue=EXAMPLE_LEAD_ISSUE,
        )

    async def issues(self) -> list[IssueSummary]:
        return [
            IssueSummary(
                number=143,
                title="Example work",
                url="https://example.invalid/issues/143",
                labels=["example"],
            )
        ]

    async def pull_requests(self) -> list[PullRequestSummary]:
        return [
            PullRequestSummary(
                number=144,
                title="Example PR",
                url="https://example.invalid/pulls/144",
                draft=True,
                state="open",
                head_ref="feat/example",
                head_sha="def456",
                base_ref="main",
            )
        ]

    async def dashboard(self) -> DashboardSummary:
        return DashboardSummary(
            repository=await self.repository_summary(),
            lead=await self.lead_state(),
            issues=await self.issues(),
            pull_requests=await self.pull_requests(),
        )


async def override_service() -> AsyncIterator[FakeService]:
    yield FakeService()


def test_health_is_explicitly_read_only() -> None:
    with TestClient(app) as client:
        response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "authority_mode": "derived_read_only",
    }


def test_dashboard_uses_mocked_service_without_network() -> None:
    app.dependency_overrides[get_service] = override_service
    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/dashboard")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["authority_mode"] == "derived_read_only"
    assert payload["repository"]["commit_sha"] == "abc123"
    assert payload["lead"]["generation"] == 8
    assert payload["lead"]["lead_issue"] == EXAMPLE_LEAD_ISSUE
    assert payload["issues"][0]["number"] == 143
    assert payload["pull_requests"][0]["head_sha"] == "def456"
