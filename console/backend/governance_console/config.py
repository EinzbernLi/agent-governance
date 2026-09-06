from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(frozen=True, slots=True)
class Settings:
    github_token: str
    repository: str
    branch: str
    lead_issue: int

    @classmethod
    def from_env(cls) -> "Settings":
        repository_raw = os.getenv("GOV_CONSOLE_REPOSITORY")
        if repository_raw is None or not repository_raw.strip():
            raise ValueError(
                "GOV_CONSOLE_REPOSITORY is required and must be in owner/name form"
            )
        repository = repository_raw.strip()
        parts = repository.split("/")
        if len(parts) != 2 or not all(parts):
            raise ValueError("GOV_CONSOLE_REPOSITORY must be in owner/name form")

        branch = os.getenv("GOV_CONSOLE_BRANCH", "main").strip() or "main"

        lead_issue_raw = os.getenv("GOV_CONSOLE_LEAD_ISSUE")
        if lead_issue_raw is None or not lead_issue_raw.strip():
            raise ValueError(
                "GOV_CONSOLE_LEAD_ISSUE is required and must be a positive integer"
            )
        try:
            lead_issue = int(lead_issue_raw.strip())
        except ValueError as exc:
            raise ValueError("GOV_CONSOLE_LEAD_ISSUE must be an integer") from exc
        if lead_issue <= 0:
            raise ValueError("GOV_CONSOLE_LEAD_ISSUE must be positive")

        return cls(
            github_token=os.getenv("GOV_CONSOLE_GITHUB_TOKEN", "").strip(),
            repository=repository,
            branch=branch,
            lead_issue=lead_issue,
        )
