import pytest


@pytest.fixture(autouse=True)
def _no_copilot_token(monkeypatch):
    """Keep the offline suite NETWORK-FREE and deterministic. With no Copilot token in the env,
    `escalation.default_llm_client()` falls back to the deferred (recording-only) stub and never
    makes a real Copilot call. Unset the token vars for every test so the suite behaves identically
    regardless of the developer's shell."""
    for var in ("COPILOT_GITHUB_TOKEN", "GH_TOKEN", "GITHUB_TOKEN"):
        monkeypatch.delenv(var, raising=False)
