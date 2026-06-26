from sec10k.llm_models import DEFAULT_MODEL, FALLBACK_MODELS


def test_default_model_is_opus_48():
    assert DEFAULT_MODEL == "claude-opus-4.8"


def test_fallback_models_include_default_and_are_well_formed():
    ids = {m["id"] for m in FALLBACK_MODELS}
    assert DEFAULT_MODEL in ids
    assert all(m.get("id") and m.get("name") for m in FALLBACK_MODELS)
