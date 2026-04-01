"""
Claude client — builds the analysis prompt and calls the Anthropic API.
"""

import anthropic
from config import cfg
from models.jira_issue import JiraIssue
from models.pull_request import PullRequest


class ClaudeClient:
    def __init__(self):
        self._client = anthropic.Anthropic(api_key=cfg.anthropic_api_key)

    def generate_dev_notes(
        self,
        issue: JiraIssue,
        prs: list[PullRequest],
        system_prompt: str,
    ) -> str:
        user_message = _build_user_message(issue, prs)

        response = self._client.messages.create(
            model=cfg.claude_model,
            max_tokens=2048,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )

        return response.content[0].text.strip()


def _build_user_message(issue: JiraIssue, prs: list[PullRequest]) -> str:
    parts = []

    # ── Ticket details ────────────────────────────────────────────────────────
    parts.append(f"# Jira Ticket: {issue.id}")
    parts.append(f"**Title:** {issue.title}\n")

    if issue.description:
        parts.append(f"**Description:**\n{issue.description.strip()}\n")

    if issue.acceptance_criteria:
        parts.append(f"**Acceptance Criteria:**\n{issue.acceptance_criteria.strip()}\n")

    # ── Pull Requests ─────────────────────────────────────────────────────────
    if not prs:
        parts.append("No linked pull requests found.")
    else:
        parts.append(f"# Pull Requests ({len(prs)} total)\n")
        for pr in prs:
            parts.append(
                f"## PR #{pr.number} — {pr.repo}\n"
                f"**Title:** {pr.title}\n"
                f"**Branch:** {pr.branch}\n"
                f"**Status:** {pr.status}\n"
                f"**URL:** {pr.url}\n"
            )
            if pr.diff:
                parts.append(f"**Diff:**\n```diff\n{pr.diff}\n```\n")
            else:
                parts.append("**Diff:** (not available)\n")

    return "\n".join(parts)
