"""
Centralised configuration — loads and validates all required environment variables.
Import `cfg` from this module; never read os.environ directly elsewhere.
"""

import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Config:
    jira_base_url: str
    jira_token: str
    jira_api_version: str
    jira_email: str          # empty string for Data Center (Bearer PAT); set for Cloud (Basic auth)
    github_token: str
    github_org: str              # scopes PR search to your org (e.g. "8x8")
    anthropic_api_key: str
    claude_model: str
    max_diff_chars: int


def load_config() -> Config:
    required = {
        "JIRA_BASE_URL": "Jira base URL (e.g. https://agile.8x8.com)",
        "JIRA_TOKEN":    "Jira PAT (Data Center) or API token (Cloud)",
        "GITHUB_TOKEN":  "GitHub personal access token",
        "ANTHROPIC_API_KEY": "Anthropic/Claude API key",
    }
    missing = [f"  {var}  — {desc}" for var, desc in required.items() if not os.environ.get(var)]
    if missing:
        raise EnvironmentError(
            "Missing required environment variables:\n" + "\n".join(missing)
            + "\n\nSet them in your .env file."
        )

    return Config(
        jira_base_url=os.environ["JIRA_BASE_URL"].rstrip("/"),
        jira_token=os.environ["JIRA_TOKEN"],
        jira_api_version=os.environ.get("JIRA_API_VERSION", "2"),
        jira_email=os.environ.get("JIRA_EMAIL", ""),
        github_token=os.environ["GITHUB_TOKEN"],
        github_org=os.environ.get("GITHUB_ORG", ""),
        anthropic_api_key=os.environ["ANTHROPIC_API_KEY"],
        claude_model=os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-6"),
        max_diff_chars=int(os.environ.get("MAX_DIFF_CHARS", "60000")),
    )


cfg = load_config()
