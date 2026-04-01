#!/usr/bin/env python3
"""
ai-auto-dev-notes-generator
────────────────────────────
Given a Jira ticket ID, fetches ticket details + linked PR diffs and uses
Claude to generate structured Dev Notes based on a chosen template.

Usage:
  python main.py PLAT-64711
  python main.py PLAT-64711 --template default
  python main.py PLAT-64711 --output notes.md
  python main.py PLAT-64711 --dry-run
  python main.py --list-templates
"""

import argparse
import sys

from config import cfg
from clients.jira_client import JiraClient
from clients.github_client import GitHubClient
from ai.claude_client import ClaudeClient
from engine.template_engine import list_templates, load_template


def main():
    parser = argparse.ArgumentParser(
        description="Generate structured Dev Notes from a Jira ticket + linked PRs.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("ticket_id", nargs="?", help="Jira ticket ID, e.g. PLAT-64711")
    parser.add_argument(
        "--template", default="default",
        help="Template name to use (default: 'default'). See --list-templates.",
    )
    parser.add_argument(
        "--output", metavar="FILE",
        help="Write output to a file instead of stdout.",
    )
    parser.add_argument(
        "--list-templates", action="store_true",
        help="Print available templates and exit.",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Fetch data and print the prompt that would be sent to Claude, but don't call the API.",
    )
    parser.add_argument(
        "--no-diff", action="store_true",
        help="Skip fetching PR diffs (faster — ticket details only).",
    )
    parser.add_argument(
        "--quiet", action="store_true",
        help="Suppress progress output — only print the generated notes (for CI/Actions use).",
    )
    args = parser.parse_args()

    if args.list_templates:
        templates = list_templates()
        print("Available templates:")
        for t in templates:
            print(f"  {t}")
        return

    if not args.ticket_id:
        parser.error("ticket_id is required unless --list-templates is used.")

    ticket_id = args.ticket_id.upper()

    log = (lambda *a, **k: None) if args.quiet else print

    # ── Step 1: Jira ──────────────────────────────────────────────────────────
    log(f"Fetching Jira ticket {ticket_id}...")
    jira = JiraClient()
    issue = jira.get_issue(ticket_id)
    log(f"  Title: {issue.title}")
    log(f"  Linked PRs found: {len(issue.pr_urls)}")

    # ── Step 2: GitHub ────────────────────────────────────────────────────────
    prs = []
    if issue.pr_urls and not args.no_diff:
        github = GitHubClient()
        for url in issue.pr_urls:
            log(f"  Fetching PR: {url}")
            pr = github.get_pr_from_url(url)
            if pr:
                diff_size = len(pr.diff)
                log(f"    [{pr.repo}] PR #{pr.number} — {pr.status} — diff: {diff_size:,} chars")
                prs.append(pr)
    elif args.no_diff:
        log("  Skipping PR diffs (--no-diff).")

    # ── Step 3: Template ──────────────────────────────────────────────────────
    log(f"\nLoading template '{args.template}'...")
    system_prompt = load_template(args.template)

    # ── Step 4: Claude ────────────────────────────────────────────────────────
    if args.dry_run:
        from ai.claude_client import _build_user_message
        print("\n--- DRY RUN: prompt that would be sent to Claude ---\n")
        print(f"SYSTEM:\n{system_prompt}\n")
        print(f"USER:\n{_build_user_message(issue, prs)}")
        return

    log(f"Generating Dev Notes with {cfg.claude_model}...")
    claude = ClaudeClient()
    notes = claude.generate_dev_notes(issue, prs, system_prompt)

    # ── Step 5: Output ────────────────────────────────────────────────────────
    if args.output:
        with open(args.output, "w") as f:
            f.write(notes + "\n")
        log(f"\nDev Notes written to: {args.output}")
    else:
        if not args.quiet:
            print(f"\n{'=' * 60}\nDEV NOTES — {ticket_id}\n{'=' * 60}\n")
        print(notes)
        if not args.quiet:
            print(f"\n{'=' * 60}")


if __name__ == "__main__":
    try:
        main()
    except EnvironmentError as e:
        print(f"Configuration error:\n{e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nAborted.")
        sys.exit(0)
