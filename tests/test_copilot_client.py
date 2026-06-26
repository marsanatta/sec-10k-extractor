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


def test_default_off_with_token_but_not_enabled(monkeypatch):
    """DEFAULT OFF: a token alone must NOT turn the tier on -- the operator must explicitly enable
    it. Without SEC10K_LLM_ESCALATION the default extract path stays deterministic ($0)."""
    monkeypatch.setenv("GH_TOKEN", "selection-test-token-not-real")
    monkeypatch.delenv("SEC10K_LLM_ESCALATION", raising=False)
    assert default_llm_client().name == "deferred"


def test_default_client_selects_copilot_when_enabled_and_threads_model(monkeypatch):
    monkeypatch.setenv("GH_TOKEN", "selection-test-token-not-real")
    monkeypatch.setenv("SEC10K_LLM_ESCALATION", "1")  # explicit operator opt-in
    captured: dict = {}

    class _StubCopilot:  # stand-in: no SDK import, no network -- selection only
        def __init__(self, model=None):
            captured["model"] = model
            self.name = f"copilot:{model or 'default'}"

        def adjudicate(self, prompt: str):
            return None

    monkeypatch.setattr(cc, "CopilotLLMClient", _StubCopilot)
    client = default_llm_client("claude-opus-4.8")
    assert client.name.startswith("copilot")
    assert not isinstance(client, DeferredLLMClient)
    assert captured["model"] == "claude-opus-4.8"  # the UI-selected model reaches the client


def test_copilot_client_swallows_errors_returns_none(monkeypatch):
    """A wired-but-failing provider must degrade to None (recording-only), never crash escalation."""
    c = cc.CopilotLLMClient(model="x")
    monkeypatch.setattr(c, "_ensure_loop", lambda: (_ for _ in ()).throw(RuntimeError("no loop")))
    assert c.adjudicate("Item 1 starts on which line?") is None


def test_copilot_client_name_carries_model():
    assert cc.CopilotLLMClient(model="gpt-5.4-mini").name == "copilot:gpt-5.4-mini"
    assert isinstance(Adjudication("3", 1, 1), Adjudication)


def test_copilot_client_default_model_is_opus_48(monkeypatch):
    monkeypatch.delenv("COPILOT_MODEL", raising=False)
    assert cc.CopilotLLMClient().name == "copilot:claude-opus-4.8"
