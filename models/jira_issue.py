from dataclasses import dataclass, field


@dataclass
class JiraIssue:
    id: str
    title: str
    description: str
    acceptance_criteria: str
    pr_urls: list[str] = field(default_factory=list)
