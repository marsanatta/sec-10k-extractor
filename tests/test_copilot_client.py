"""Offline tests for the graceful-fallback escalation-provider SELECTION. These never make a real
Copilot call: the real client is monkeypatched to a stub so we test only that the right provider
is chosen by token presence. The real network path is exercised separately, on demand, with a
token (see ANALYSIS / eval), never in the CI suite."""
import sec10k.copilot_client as cc
from sec10k.escalation import Adjudication, DeferredLLMClient, default_llm_client


def test_default_client_is_deferred_without_token(monkeypatch):
    for var in ("COPILOT_GITHUB_TOKEN", "GH_TOKEN", "GITHUB_TOKEN"):
        monkeypatch.delenv(var, raising=False)
    assert default_llm_client().name == "deferred"


def test_default_client_selects_copilot_with_token(monkeypatch):
    monkeypatch.setenv("GH_TOKEN", "selection-test-token-not-real")

    class _StubCopilot:  # stand-in: no SDK import, no network -- selection only
        name = "copilot:stub"

        def adjudicate(self, prompt: str):
            return None

    monkeypatch.setattr(cc, "CopilotLLMClient", _StubCopilot)
    client = default_llm_client()
    assert client.name.startswith("copilot")
    assert not isinstance(client, DeferredLLMClient)


def test_copilot_client_swallows_errors_returns_none(monkeypatch):
    """A wired-but-failing provider must degrade to None (recording-only), never crash escalation."""
    c = cc.CopilotLLMClient(model="x")
    monkeypatch.setattr(c, "_ensure_loop", lambda: (_ for _ in ()).throw(RuntimeError("no loop")))
    assert c.adjudicate("Item 1 starts on which line?") is None


def test_copilot_client_name_carries_model():
    assert cc.CopilotLLMClient(model="gpt-5.4-mini").name == "copilot:gpt-5.4-mini"
    assert isinstance(Adjudication("3", 1, 1), Adjudication)
