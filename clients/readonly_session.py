"""
A requests Session that raises an error if any non-GET method is attempted.
Used by all external clients to enforce read-only access.
"""

import requests


class ReadOnlySession(requests.Session):
    """Wraps requests.Session and blocks all mutating HTTP methods."""

    def request(self, method: str, url, **kwargs):
        if method.upper() != "GET":
            raise PermissionError(
                f"ReadOnlySession blocked a '{method.upper()}' request to {url}. "
                "This tool is read-only — no writes to Jira or GitHub are permitted."
            )
        return super().request(method, url, **kwargs)
