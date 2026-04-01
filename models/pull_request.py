from dataclasses import dataclass


@dataclass
class PullRequest:
    url: str
    number: int
    owner: str
    repo: str
    title: str
    branch: str
    status: str   # "open" | "closed" | "merged"
    diff: str     # unified diff, possibly truncated
