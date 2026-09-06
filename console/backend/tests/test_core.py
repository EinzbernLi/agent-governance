from __future__ import annotations

import asyncio

from governance_console.config import Settings
from governance_console.core import ConsoleService, parse_lead_state


EXAMPLE_VERSION = "9.9.9"
EXAMPLE_LEAD_ISSUE = 73


def test_no_claim_is_unknown() -> None:
    state = parse_lead_state([], lead_issue=EXAMPLE_LEAD_ISSUE)
    assert state.status == "unknown"
    assert state.generation is None


def test_current_style_g8_claim_with_bound_activation_is_active() -> None:
    comments = [
        {
            "id": 100,
            "body": "[GOVERNANCE-LEAD-CLAIM-G8-MANAGEMENT-SYSTEM]\n",
        },
        {
            "id": 101,
            "body": (
                "[GOVERNANCE-LEAD-G8-ACTIVATION-VERIFY]\n"
                "active_lead_status: ACTIVE\n"
                "active_claim_ref: 100\n"
            ),
        },
    ]
    state = parse_lead_state(comments, lead_issue=EXAMPLE_LEAD_ISSUE)
    assert state.status == "active"
    assert state.generation == 8
    assert state.claim_comment_id == 100
    assert state.activation_comment_id == 101


def test_duplicate_latest_generation_is_conflict() -> None:
    comments = [
        {"id": 100, "body": "[GOVERNANCE-LEAD-CLAIM-G7]\n"},
        {"id": 200, "body": "[GOVERNANCE-LEAD-CLAIM-G8-A]\n"},
        {"id": 201, "body": "[GOVERNANCE-LEAD-CLAIM-G8-B]\n"},
        {
            "id": 202,
            "body": (
                "[GOVERNANCE-LEAD-G8-ACTIVATION-VERIFY]\n"
                "active_lead_status: ACTIVE\n"
                "active_claim_ref: 200\n"
            ),
        },
    ]
    state = parse_lead_state(comments, lead_issue=EXAMPLE_LEAD_ISSUE)
    assert state.status == "conflict"
    assert state.generation == 8
    assert state.conflict_comment_ids == [200, 201]
    assert state.activation_comment_id is None


def test_claim_without_verification_is_not_active() -> None:
    state = parse_lead_state(
        [{"id": 300, "body": "[GOVERNANCE-LEAD-CLAIM-G8]\n"}],
        lead_issue=EXAMPLE_LEAD_ISSUE,
    )
    assert state.status == "claimed_unverified"
    assert state.generation == 8


def test_mismatched_activation_claim_ref_is_not_active() -> None:
    comments = [
        {"id": 400, "body": "[GOVERNANCE-LEAD-CLAIM-G8]\n"},
        {
            "id": 401,
            "body": (
                "[GOVERNANCE-LEAD-G8-ACTIVATION-VERIFY]\n"
                "active_lead_status: ACTIVE\n"
                "active_claim_ref: 399\n"
            ),
        },
    ]
    state = parse_lead_state(comments, lead_issue=EXAMPLE_LEAD_ISSUE)
    assert state.status == "claimed_unverified"
    assert state.activation_comment_id is None


class FakeGitHubClient:
    async def get_branch(self, branch: str):
        assert branch == "main"
        return {"commit": {"sha": "abc123"}}

    async def get_contents_text(self, path: str, ref: str):
        assert path == "VERSION"
        assert ref == "abc123"
        return f"{EXAMPLE_VERSION}\n"

    async def get_issue_comments(self, issue_number: int):
        assert issue_number == EXAMPLE_LEAD_ISSUE
        return [
            {
                "id": 10,
                "body": "[GOVERNANCE-LEAD-CLAIM-G8-MANAGEMENT-SYSTEM]\n",
            },
            {
                "id": 11,
                "body": (
                    "[GOVERNANCE-LEAD-G8-ACTIVATION-VERIFY]\n"
                    "active_lead_status: ACTIVE\n"
                    "active_claim_ref: 10\n"
                ),
            },
        ]

    async def get_open_issues(self):
        return [
            {
                "number": 143,
                "title": "Example work",
                "html_url": "https://example.invalid/issues/143",
                "updated_at": "2030-01-02T00:00:00Z",
                "labels": [{"name": "example"}],
            }
        ]

    async def get_open_pulls(self):
        return [
            {
                "number": 144,
                "title": "Example PR",
                "html_url": "https://example.invalid/pulls/144",
                "draft": True,
                "state": "open",
                "head": {"ref": "feat/example", "sha": "def456"},
                "base": {"ref": "main"},
                "updated_at": "2030-01-02T00:00:00Z",
            }
        ]


def test_dashboard_uses_exact_branch_sha_and_mocked_payloads() -> None:
    settings = Settings(
        github_token="",
        repository="example/governance",
        branch="main",
        lead_issue=EXAMPLE_LEAD_ISSUE,
    )
    service = ConsoleService(FakeGitHubClient(), settings)  # type: ignore[arg-type]
    dashboard = asyncio.run(service.dashboard())

    assert dashboard.authority_mode == "derived_read_only"
    assert dashboard.repository.commit_sha == "abc123"
    assert dashboard.repository.version == EXAMPLE_VERSION
    assert dashboard.lead.status == "active"
    assert dashboard.lead.generation == 8
    assert dashboard.issues[0].number == 143
    assert dashboard.pull_requests[0].head_sha == "def456"
