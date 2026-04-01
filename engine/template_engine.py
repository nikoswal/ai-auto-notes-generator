"""
Discovers and loads prompt templates from the templates/ directory.
Each template is a plain .md file containing instructions for Claude.
"""

import os

_TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "..", "templates")


def list_templates() -> list[str]:
    """Returns available template names (without .md extension)."""
    return sorted(
        f[:-3] for f in os.listdir(_TEMPLATES_DIR)
        if f.endswith(".md")
    )


def load_template(name: str) -> str:
    path = os.path.join(_TEMPLATES_DIR, f"{name}.md")
    if not os.path.exists(path):
        available = ", ".join(list_templates()) or "none"
        raise FileNotFoundError(
            f"Template '{name}' not found. Available templates: {available}"
        )
    with open(path) as f:
        return f.read()
