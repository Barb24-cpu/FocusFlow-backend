# TODO: Implement this file
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import GitHubAccount, User
from app.security import encrypt_token
from app.services.github_service import GitHubService

router = APIRouter()


# --- Pydantic Request / Response Schemas ---

class GitHubConnectRequest(BaseModel):
    access_token: str = Field(..., min_length=10, description="GitHub Personal Access Token")
    github_username: str | None = Field(
        default=None,
        description="Optional override; if omitted, resolved directly from GitHub /user",
    )


class GitHubConnectionResponse(BaseModel):
    connected: bool
    github_username: str
    connected_at: datetime


# --- Helper Dependency ---

def get_user_github_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> GitHubAccount:
    account = (
        db.query(GitHubAccount)
        .filter(GitHubAccount.user_id == current_user.id)
        .first()
    )
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="GitHub account is not connected. Call POST /api/github/connect first.",
        )
    return account


# --- Section 7 Endpoints ---

@router.post("/connect", response_model=GitHubConnectionResponse, status_code=status.HTTP_201_CREATED)
async def connect_github_account(
    payload: GitHubConnectRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """POST /api/github/connect — Verify PAT, encrypt token, and link GitHub account."""
    gh_service = GitHubService(raw_token=payload.access_token)
    gh_profile = await gh_service.verify_token_and_get_user()

    resolved_username = payload.github_username or gh_profile["github_username"]
    encrypted = encrypt_token(payload.access_token)

    existing = (
        db.query(GitHubAccount)
        .filter(GitHubAccount.user_id == current_user.id)
        .first()
    )

    if existing:
        existing.github_username = resolved_username
        existing.access_token_encrypted = encrypted
        existing.connected_at = datetime.utcnow()
        account = existing
    else:
        account = GitHubAccount(
            user_id=current_user.id,
            github_username=resolved_username,
            access_token_encrypted=encrypted,
            connected_at=datetime.utcnow(),
        )
        db.add(account)

    db.commit()
    db.refresh(account)

    return GitHubConnectionResponse(
        connected=True,
        github_username=account.github_username,
        connected_at=account.connected_at,
    )


@router.delete("/disconnect", status_code=status.HTTP_200_OK)
def disconnect_github_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """DELETE /api/github/disconnect — Remove user's GitHub connection."""
    account = (
        db.query(GitHubAccount)
        .filter(GitHubAccount.user_id == current_user.id)
        .first()
    )
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No connected GitHub account found.",
        )

    db.delete(account)
    db.commit()
    return {"connected": False, "message": "GitHub account disconnected successfully."}


@router.get("/repositories")
async def list_github_repositories(
    account: GitHubAccount = Depends(get_user_github_account),
):
    """GET /api/github/repositories — List repositories for the connected GitHub user."""
    service = GitHubService(encrypted_token=account.access_token_encrypted)
    repositories = await service.list_repositories()
    return {"github_username": account.github_username, "repositories": repositories}


@router.get("/repositories/{owner}/{repo}/commits")
async def get_repository_commits(
    owner: str,
    repo: str,
    account: GitHubAccount = Depends(get_user_github_account),
):
    """GET /api/github/repositories/:owner/:repo/commits — Fetch recent commits."""
    service = GitHubService(encrypted_token=account.access_token_encrypted)
    commits = await service.get_repo_commits(owner=owner, repo=repo)
    return {"repository": f"{owner}/{repo}", "commits": commits}


@router.get("/issues")
async def list_github_issues(
    account: GitHubAccount = Depends(get_user_github_account),
):
    """GET /api/github/issues — Fetch open issues for the connected GitHub user."""
    service = GitHubService(encrypted_token=account.access_token_encrypted)
    issues = await service.list_open_issues(github_username=account.github_username)
    return {"github_username": account.github_username, "issues": issues}


@router.get("/pulls")
async def list_github_pull_requests(
    account: GitHubAccount = Depends(get_user_github_account),
):
    """GET /api/github/pulls — Fetch open pull requests for the connected GitHub user."""
    service = GitHubService(encrypted_token=account.access_token_encrypted)
    pulls = await service.list_pull_requests(github_username=account.github_username)
    return {"github_username": account.github_username, "pulls": pulls}