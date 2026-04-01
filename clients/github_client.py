"""
GitHub client — fetches pull request metadata and unified diffs.
"""

import re
import requests
from config import cfg
from models.pull_request import PullRequest
from clients.readonly_session import ReadOnlySession

_PR_URL_RE = re.compile(
    r"github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/pull/(?P<number>\d+)"
)


class GitHubClient:
    def __init__(self):
        self._session = ReadOnlySession()
        self._session.headers.update({
            "Authorization": f"Bearer {cfg.github_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        })

    def _get(self, path: str, **kwargs) -> dict | list:
        resp = self._session.get(f"https://api.github.com{path}", timeout=15, **kwargs)
        resp.raise_for_status()
        return resp.json()

    def parse_pr_url(self, url: str) -> tuple[str, str, int] | None:
        """Returns (owner, repo, pr_number) or None if the URL doesn't match."""
        m = _PR_URL_RE.search(url)
        if not m:
            return None
        return m.group("owner"), m.group("repo"), int(m.group("number"))

    def get_pr(self, owner: str, repo: str, number: int) -> PullRequest:
        pr_data = self._get(f"/repos/{owner}/{repo}/pulls/{number}")

        # Determine status
        if pr_data.get("merged_at"):
            status = "merged"
        elif pr_data.get("state") == "open":
            status = "open"
        else:
            status = "closed"

        diff = self._get_diff(owner, repo, number)

        return PullRequest(
            url=pr_data["html_url"],
            number=number,
            owner=owner,
            repo=repo,
            title=pr_data["title"],
            branch=pr_data["head"]["ref"],
            status=status,
            diff=diff,
        )

    def search_prs_for_ticket(self, ticket_id: str) -> list[str]:
        """
        Searches GitHub for PRs whose source branch name contains the ticket ID.
        Scoped to GITHUB_ORG if configured.
        Returns a list of PR HTML URLs.
        """
        query = f"{ticket_id} is:pr"
        if cfg.github_org:
            query += f" org:{cfg.github_org}"

        data = self._get("/search/issues", params={"q": query, "per_page": 25})

        urls = []
        for item in data.get("items", []):
            parsed = self.parse_pr_url(item.get("html_url", ""))
            if not parsed:
                continue
            owner, repo, number = parsed
            try:
                pr_data = self._get(f"/repos/{owner}/{repo}/pulls/{number}")
                branch = pr_data["head"]["ref"]
                if ticket_id.upper() in branch.upper():
                    urls.append(item["html_url"])
            except Exception as e:
                print(f"  [warn] Could not fetch PR details for {item.get('html_url')}: {e}")

        return urls

    def get_pr_from_url(self, url: str) -> PullRequest | None:
        parsed = self.parse_pr_url(url)
        if not parsed:
            print(f"  [warn] Could not parse PR URL: {url}")
            return None
        owner, repo, number = parsed
        return self.get_pr(owner, repo, number)

    def _get_diff(self, owner: str, repo: str, number: int) -> str:
        """Fetches file patches and assembles a unified diff string."""
        files = self._get(f"/repos/{owner}/{repo}/pulls/{number}/files")

        chunks = []
        total_chars = 0

        for f in files:
            filename = f.get("filename", "")
            patch = f.get("patch", "")
            if not patch:
                # Binary or renamed-only file
                chunks.append(f"--- {filename}\n(no diff available — binary or renamed)\n")
                continue

            chunk = f"--- {filename}\n{patch}\n"
            if total_chars + len(chunk) > cfg.max_diff_chars:
                remaining = cfg.max_diff_chars - total_chars
                if remaining > 0:
                    chunks.append(chunk[:remaining])
                chunks.append(f"\n... [diff truncated at {cfg.max_diff_chars} chars] ...\n")
                break

            chunks.append(chunk)
            total_chars += len(chunk)

        return "".join(chunks)
