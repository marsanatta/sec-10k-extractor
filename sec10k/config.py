import os
from pathlib import Path

CACHE_DIR = Path(os.environ.get("SEC10K_CACHE_DIR", ".cache/sec10k"))


def get_user_agent() -> str:
    """SEC fair-access requires a descriptive User-Agent (name + email). It is read
    from the environment so no personal contact is hardcoded into this public repo."""
    ua = os.environ.get("SEC_EDGAR_USER_AGENT", "").strip()
    if not ua:
        raise RuntimeError(
            "SEC_EDGAR_USER_AGENT is not set. SEC requires a descriptive User-Agent "
            "such as 'Jane Doe jane@example.com'. Export it before fetching filings."
        )
    return ua
