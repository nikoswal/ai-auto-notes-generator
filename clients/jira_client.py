"""
Jira client — fetches issue details and linked pull requests.

Supports:
  - Jira Data Center / Server: Bearer PAT auth, API v2
  - Jira Cloud (atlassian.net): Basic auth (email:token), API v3
"""

import base64
import re
import requests
from config import cfg
from models.jira_issue import JiraIssue
from clients.readonly_session import ReadOnlySession


class JiraClient:
    def __init__(self):
        self._base = cfg.jira_base_url
        self._v = cfg.jira_api_version
        self._session = ReadOnlySession()

        if cfg.jira_email:
            creds = base64.b64encode(f"{cfg.jira_email}:{cfg.jira_token}".encode()).decode()
            self._session.headers["Authorization"] = f"Basic {creds}"
        else:
            self._session.headers["Authorization"] = f"Bearer {cfg.jira_token}"

        self._session.headers["Accept"] = "application/json"

    def _get(self, path: str, **kwargs) -> dict:
        resp = self._session.get(f"{self._base}{path}", timeout=15, **kwargs)
        resp.raise_for_status()
        return resp.json()

    def get_issue(self, ticket_id: str) -> JiraIssue:
        data = self._get(
            f"/rest/api/{self._v}/issue/{ticket_id}",
            params={"fields": "summary,description,comment,customfield_10016"},
        )
        fields = data["fields"]
        issue_id = data["id"]

        title = fields.get("summary", "")
        description = _extract_text(fields.get("description"))
        acceptance_criteria = _extract_acceptance_criteria(fields)
        pr_urls = self.get_linked_pull_requests(ticket_id, issue_id)

        return JiraIssue(
            id=ticket_id,
            title=title,
            description=description,
            acceptance_criteria=acceptance_criteria,
            pr_urls=pr_urls,
        )

    def get_linked_pull_requests(self, ticket_id: str, issue_id: str = None) -> list[str]:
        """
        Searches GitHub for PRs whose title or branch name mentions the ticket ID,
        scoped to GITHUB_ORG if set. This bypasses the Jira dev-status plugin
        which requires cookie-based auth not available via PAT.
        """
        from clients.github_client import GitHubClient
        return GitHubClient().search_prs_for_ticket(ticket_id)


def _extract_text(field) -> str:
    """Parse both Atlassian Document Format (ADF) and plain string."""
    if not field:
        return ""
    if isinstance(field, str):
        return field
    # ADF — recursively extract text nodes
    if isinstance(field, dict):
        return _adf_to_text(field)
    return ""


def _adf_to_text(node: dict, depth: int = 0) -> str:
    """Minimal ADF → plain text converter."""
    node_type = node.get("type", "")
    text = node.get("text", "")
    parts = []

    if text:
        parts.append(text)

    for child in node.get("content", []):
        parts.append(_adf_to_text(child, depth + 1))

    result = "".join(parts)

    # Add newlines after block elements
    if node_type in ("paragraph", "heading", "listItem", "bulletList", "orderedList"):
        result = result.strip() + "\n"

    return result


def _extract_acceptance_criteria(fields: dict) -> str:
    """
    Tries common locations for acceptance criteria:
    1. A custom field named 'Acceptance Criteria'
    2. Text under an '## Acceptance Criteria' heading in the description
    """
    # Common custom field IDs for AC
    for field_key in ("customfield_10016", "customfield_10034", "customfield_10035"):
        val = fields.get(field_key)
        if val:
            return _extract_text(val)

    # Fall back to searching description text
    description = _extract_text(fields.get("description"))
    match = re.search(
        r"(?i)acceptance criteria[:\s]*\n+(.*?)(?=\n{2,}|\Z)",
        description,
        re.DOTALL,
    )
    if match:
        return match.group(1).strip()

    return ""
