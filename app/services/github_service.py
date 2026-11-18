# TODO: Implement this file
import httpx
from fastapi import HTTPException, status
from app.security import decrypt_token


class GitHubService:
    BASE_URL = "https://api.github.com"

    def __init__(self, encrypted_token: str | None = None, raw_token: str | None = None):
        if raw_token:
            token = raw_token
        elif encrypted_token:
            token = decrypt_token(encrypted_token)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="GitHub access token is missing",
            )

        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    async def _request(self, method: str, path: str, params: dict | None = None):
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.request(
                method=method,
                url=f"{self.BASE_URL}{path}",
                headers=self.headers,
                params=params,
            )

        if response.status_code == 401:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="GitHub token is invalid or expired. Please reconnect your account.",
            )
        if response.status_code == 403:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="GitHub API rate limit exceeded or insufficient token scopes.",
            )
        if response.status_code == 404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Requested GitHub resource or repository was not found.",
            )
        if response.status_code >= 400:
            raise HTTPException(
                status_code=response.status_code,
                detail="GitHub API request failed.",
            )

        return response.json()

    async def verify_token_and_get_user(self) -> dict:
        """Validates a newly supplied PAT during /api/github/connect."""
        data = await self._request("GET", "/user")
        return {
            "github_username": data.get("login"),
            "avatar_url": data.get("avatar_url"),
            "profile_url": data.get("html_url"),
        }

    async def list_repositories(self, per_page: int = 30) -> list[dict]:
        """Fetches authenticated user's repositories formatted for FocusFlow Projects."""
        repos = await self._request(
            "GET",
            "/user/repos",
            params={"sort": "updated", "affiliation": "owner,collaborator", "per_page": per_page},
        )
        return [
            {
                "id": repo["id"],
                "name": repo["name"],
                "full_name": repo["full_name"],  # Matches projects.github_repo ("owner/repo")
                "description": repo.get("description"),
                "private": repo["private"],
                "language": repo.get("language"),
                "stargazers_count": repo.get("stargazers_count", 0),
                "open_issues_count": repo.get("open_issues_count", 0),
                "html_url": repo["html_url"],
                "updated_at": repo["updated_at"],
            }
            for repo in repos
        ]

    async def get_repo_commits(self, owner: str, repo: str, per_page: int = 20) -> list[dict]:
        """Fetches recent commits for a specific repository."""
        commits = await self._request(
            "GET",
            f"/repos/{owner}/{repo}/commits",
            params={"per_page": per_page},
        )
        return [
            {
                "sha": item["sha"][:7],
                "full_sha": item["sha"],
                "message": item["commit"]["message"].splitlines()[0],
                "author_name": item["commit"]["author"]["name"],
                "author_username": item["author"]["login"] if item.get("author") else None,
                "date": item["commit"]["author"]["date"],
                "html_url": item["html_url"],
            }
            for item in commits
        ]

    async def list_open_issues(self, github_username: str, per_page: int = 20) -> list[dict]:
        """Fetches open issues authored by or assigned to the connected GitHub user."""
        data = await self._request(
            "GET",
            "/search/issues",
            params={
                "q": f"involves:{github_username} is:issue is:open",
                "sort": "updated",
                "order": "desc",
                "per_page": per_page,
            },
        )
        return [
            {
                "id": issue["id"],
                "number": issue["number"],
                "title": issue["title"],
                "state": issue["state"],
                "repository": issue["repository_url"].split("/repos/")[-1],
                "labels": [lbl["name"] for lbl in issue.get("labels", [])],
                "created_at": issue["created_at"],
                "updated_at": issue["updated_at"],
                "html_url": issue["html_url"],
            }
            for issue in data.get("items", [])
        ]

    async def list_pull_requests(self, github_username: str, per_page: int = 20) -> list[dict]:
        """Fetches open pull requests involving the connected GitHub user."""
        data = await self._request(
            "GET",
            "/search/issues",
            params={
                "q": f"involves:{github_username} is:pr is:open",
                "sort": "updated",
                "order": "desc",
                "per_page": per_page,
            },
        )
        return [
            {
                "id": pr["id"],
                "number": pr["number"],
                "title": pr["title"],
                "state": pr["state"],
                "draft": pr.get("draft", False),
                "repository": pr["repository_url"].split("/repos/")[-1],
                "created_at": pr["created_at"],
                "updated_at": pr["updated_at"],
                "html_url": pr["html_url"],
            }
            for pr in data.get("items", [])
        ]