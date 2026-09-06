from __future__ import annotations

import pytest

from governance_console.config import Settings


EXAMPLE_REPOSITORY = "example/governance"
EXAMPLE_LEAD_ISSUE = "73"


def _set_required(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GOV_CONSOLE_REPOSITORY", EXAMPLE_REPOSITORY)
    monkeypatch.setenv("GOV_CONSOLE_LEAD_ISSUE", EXAMPLE_LEAD_ISSUE)


def test_explicit_repository_and_lead_issue_succeed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_required(monkeypatch)
    monkeypatch.setenv("GOV_CONSOLE_BRANCH", "release")
    monkeypatch.setenv("GOV_CONSOLE_GITHUB_TOKEN", "example-token")

    settings = Settings.from_env()

    assert settings.repository == EXAMPLE_REPOSITORY
    assert settings.lead_issue == int(EXAMPLE_LEAD_ISSUE)
    assert settings.branch == "release"
    assert settings.github_token == "example-token"


@pytest.mark.parametrize("value", [None, "", "   "])
def test_missing_or_blank_repository_fails_closed(
    monkeypatch: pytest.MonkeyPatch, value: str | None
) -> None:
    monkeypatch.setenv("GOV_CONSOLE_LEAD_ISSUE", EXAMPLE_LEAD_ISSUE)
    if value is None:
        monkeypatch.delenv("GOV_CONSOLE_REPOSITORY", raising=False)
    else:
        monkeypatch.setenv("GOV_CONSOLE_REPOSITORY", value)

    with pytest.raises(ValueError, match="GOV_CONSOLE_REPOSITORY is required"):
        Settings.from_env()


@pytest.mark.parametrize("value", ["example", "/governance", "example/", "a/b/c"])
def test_repository_must_be_owner_name(
    monkeypatch: pytest.MonkeyPatch, value: str
) -> None:
    monkeypatch.setenv("GOV_CONSOLE_REPOSITORY", value)
    monkeypatch.setenv("GOV_CONSOLE_LEAD_ISSUE", EXAMPLE_LEAD_ISSUE)

    with pytest.raises(ValueError, match="owner/name form"):
        Settings.from_env()


@pytest.mark.parametrize("value", [None, "", "   "])
def test_missing_or_blank_lead_issue_fails_closed(
    monkeypatch: pytest.MonkeyPatch, value: str | None
) -> None:
    monkeypatch.setenv("GOV_CONSOLE_REPOSITORY", EXAMPLE_REPOSITORY)
    if value is None:
        monkeypatch.delenv("GOV_CONSOLE_LEAD_ISSUE", raising=False)
    else:
        monkeypatch.setenv("GOV_CONSOLE_LEAD_ISSUE", value)

    with pytest.raises(ValueError, match="GOV_CONSOLE_LEAD_ISSUE is required"):
        Settings.from_env()


def test_non_integer_lead_issue_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GOV_CONSOLE_REPOSITORY", EXAMPLE_REPOSITORY)
    monkeypatch.setenv("GOV_CONSOLE_LEAD_ISSUE", "not-an-integer")

    with pytest.raises(ValueError, match="must be an integer"):
        Settings.from_env()


@pytest.mark.parametrize("value", ["0", "-1"])
def test_non_positive_lead_issue_fails_closed(
    monkeypatch: pytest.MonkeyPatch, value: str
) -> None:
    monkeypatch.setenv("GOV_CONSOLE_REPOSITORY", EXAMPLE_REPOSITORY)
    monkeypatch.setenv("GOV_CONSOLE_LEAD_ISSUE", value)

    with pytest.raises(ValueError, match="must be positive"):
        Settings.from_env()


def test_branch_defaults_to_main_when_omitted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_required(monkeypatch)
    monkeypatch.delenv("GOV_CONSOLE_BRANCH", raising=False)

    settings = Settings.from_env()

    assert settings.branch == "main"


def test_blank_branch_defaults_to_main(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_required(monkeypatch)
    monkeypatch.setenv("GOV_CONSOLE_BRANCH", "   ")

    settings = Settings.from_env()

    assert settings.branch == "main"


def test_token_is_optional(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_required(monkeypatch)
    monkeypatch.delenv("GOV_CONSOLE_GITHUB_TOKEN", raising=False)

    settings = Settings.from_env()

    assert settings.github_token == ""
