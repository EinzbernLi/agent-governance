# Governance Console

Governance Console is an **optional, derived, read-only operator surface** for a configured governance repository. It is not a third product module.

It does not replace GitHub Issues, pull requests, repository governance files, Lead Claim comments, Task/Result evidence, or LPRL artifacts as durable authority. It is not a Lead, dispatcher, acceptance authority, or mutation authority.

## Phase A

The first slice intentionally has no database and no GitHub write endpoints. It reads the explicitly configured repository and Lead Issue and exposes a compact dashboard through a FastAPI backend and React frontend.

### Backend

Requirements: Python 3.11+.

```bash
cd console/backend
python -m venv .venv
# activate the environment
pip install -e '.[dev]'
# configure the variables shown in ../.env.example in your shell
uvicorn governance_console.main:app --reload
```

Configuration:

- `GOV_CONSOLE_REPOSITORY`: **required**. Supply the target repository explicitly in `owner/name` form. There is no central/private repository default.
- `GOV_CONSOLE_LEAD_ISSUE`: **required**. Supply the positive Issue number used as the configured Lead Claim sink. There is no default Lead Issue.
- `GOV_CONSOLE_BRANCH`: optional; defaults to `main`.
- `GOV_CONSOLE_GITHUB_TOKEN`: optional. When supplied, use a token with read access to the configured repository.

Repository and Lead Issue are never inferred from Git remotes, the working directory, `.agent/**`, Issue enumeration, the current GitHub account, or another ambient source.

Backend checks:

```bash
python -m compileall governance_console tests
pytest
```

### Frontend

Requirements: Node.js 20+.

The committed `package-lock.json` is the deterministic dependency input used by CI.

```bash
cd console/frontend
npm ci
npm run typecheck
npm run build
npm run dev
```

During Vite development, `/api` is proxied to `http://127.0.0.1:8000`. For a separately deployed frontend, set `VITE_API_BASE` to the backend origin.

## CI

Every pull request is still subject to the repository-wide required `governance-ci` check. Changes under `console/**` (or to the Console CI workflow itself) additionally run the read-only `console-ci` job, which installs the backend test dependencies, compiles and tests the backend, installs frontend dependencies with `npm ci`, typechecks, builds, and verifies that tracked repository state remains clean.

Neither CI workflow needs a live Governance Console GitHub token for these tests.

## Authority boundary

The console follows these fail-closed rules:

- Lead state is derived only from explicit canonical Issue comment markers.
- Duplicate latest-generation claims surface as `conflict`.
- Missing claims surface as `unknown`.
- A claim without a matching ACTIVE activation verification bound to the exact selected claim surfaces as `claimed_unverified`.
- Retrieval/parsing failures are returned as errors; the UI must not invent ACTIVE state.
- Repository/version summaries carry the exact branch and commit SHA used for the view.
- Pagination refuses to silently truncate an incomplete derived view.

Phase A contains no create/edit/close Issue action, merge action, Lead Claim writer, Task dispatcher, acceptance path, background daemon, cache database, or downstream mutation path.
