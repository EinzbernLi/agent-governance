from __future__ import annotations

from collections.abc import AsyncIterator

import httpx
from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import Settings
from .core import (
    ConsoleService,
    DashboardSummary,
    GitHubClient,
    IssueSummary,
    LeadState,
    PullRequestSummary,
    RepositorySummary,
)


app = FastAPI(
    title="Governance Console API",
    version="0.1.0",
    description="Derived read-only view over durable GitHub governance facts.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)


async def get_service() -> AsyncIterator[ConsoleService]:
    settings = Settings.from_env()
    client = GitHubClient(settings)
    try:
        yield ConsoleService(client, settings)
    finally:
        await client.close()


@app.exception_handler(httpx.HTTPError)
async def github_http_error(_: Request, exc: httpx.HTTPError) -> JSONResponse:
    return JSONResponse(
        status_code=502,
        content={
            "detail": "GitHub retrieval failed; no governance state was inferred.",
            "error_type": type(exc).__name__,
        },
    )


@app.exception_handler(ValueError)
async def derived_state_error(_: Request, exc: ValueError) -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content={
            "detail": "Governance state is unavailable or malformed; fail-closed.",
            "error": str(exc),
        },
    )


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "authority_mode": "derived_read_only"}


@app.get("/api/v1/repository", response_model=RepositorySummary)
async def repository(
    service: ConsoleService = Depends(get_service),
) -> RepositorySummary:
    return await service.repository_summary()


@app.get("/api/v1/lead", response_model=LeadState)
async def lead(service: ConsoleService = Depends(get_service)) -> LeadState:
    return await service.lead_state()


@app.get("/api/v1/issues", response_model=list[IssueSummary])
async def issues(service: ConsoleService = Depends(get_service)) -> list[IssueSummary]:
    return await service.issues()


@app.get("/api/v1/pull-requests", response_model=list[PullRequestSummary])
async def pull_requests(
    service: ConsoleService = Depends(get_service),
) -> list[PullRequestSummary]:
    return await service.pull_requests()


@app.get("/api/v1/dashboard", response_model=DashboardSummary)
async def dashboard(
    service: ConsoleService = Depends(get_service),
) -> DashboardSummary:
    return await service.dashboard()
