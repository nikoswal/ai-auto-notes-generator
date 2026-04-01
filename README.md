# ai-auto-dev-notes-generator

A CLI tool for AI hackathon that takes a Jira ticket ID, fetches linked Pull Requests, analyses the code diffs, and automatically generates structured Dev Notes using Claude.

## How it works

```
Jira ticket ID
    └─► Jira API  ──► ticket title, description, acceptance criteria + linked PR URLs
                          └─► GitHub API  ──► code diffs for each PR
                                                └─► Claude API  ──► structured Dev Notes
```

## Setup

**1. Clone and create virtualenv**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**2. Configure credentials**
```bash
cp .env.example .env
# Edit .env and fill in your tokens
```

**3. Verify connectivity**
```bash
python check_connectivity.py
```

## Usage

```bash
# Basic — generate dev notes for a ticket
python main.py PLAT-64711

# Choose a different template
python main.py PLAT-64711 --template default

# Write output to a file
python main.py PLAT-64711 --output notes.md

# See what would be sent to Claude without calling the API
python main.py PLAT-64711 --dry-run

# Skip PR diffs (faster, ticket details only)
python main.py PLAT-64711 --no-diff

# List available templates
python main.py --list-templates
```

## Environment variables

| Variable | Required | Description |
|---|---|---|
| `JIRA_BASE_URL` | Yes | e.g. `https://agile.8x8.com` |
| `JIRA_TOKEN` | Yes | PAT for Data Center; API token for Cloud |
| `JIRA_API_VERSION` | No | `2` (default, Data Center) or `3` (Cloud) |
| `JIRA_EMAIL` | No | Set for Jira Cloud Basic auth; leave unset for Data Center Bearer PAT |
| `GITHUB_TOKEN` | Yes | Personal access token with `repo` scope |
| `ANTHROPIC_API_KEY` | Yes | Claude API key |
| `CLAUDE_MODEL` | No | Default: `claude-sonnet-4-6` |
| `MAX_DIFF_CHARS` | No | Max diff size sent to Claude (default: `60000`) |
| `JIRA_TEST_TICKET` | No | Used only by `check_connectivity.py` |

## Adding a custom template

1. Create a new `.md` file in the `templates/` directory, e.g. `templates/release_notes.md`
2. Write instructions to Claude describing how you want the output structured
3. Use it: `python main.py PLAT-64711 --template release_notes`

No code changes needed — the tool auto-discovers all `.md` files in `templates/`.

## Project structure

```
├── main.py                  # CLI entrypoint
├── config.py                # Loads & validates env vars
├── clients/
│   ├── jira_client.py       # Jira API interactions
│   └── github_client.py     # GitHub API interactions
├── ai/
│   └── claude_client.py     # Claude API — generates dev notes
├── engine/
│   └── template_engine.py   # Discovers and loads templates
├── models/
│   ├── jira_issue.py        # JiraIssue dataclass
│   └── pull_request.py      # PullRequest dataclass
├── templates/
│   └── default.md           # Default dev notes template
├── check_connectivity.py    # Smoke test for all three APIs
├── requirements.txt
└── .env                     # Your credentials (never committed)
```
