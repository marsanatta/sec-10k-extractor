"""Offline correctness guard for the eval harness's parallel runner: rows MUST come back in input
order and a per-filing failure MUST be isolated (one bad filing does not sink the report). The
SPEEDUP itself is a process-pool property validated by a LIVE A/B, not an offline mock -- a
sleep-based mock gives false confidence here (it did, for the earlier thread version: it "passed"
offline yet a process is what actually overlaps the real GIL-held work). So this test exercises the
order/isolation logic via the in-process path (EVAL_WORKERS<=1), where monkeypatch is visible."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "eval"))
import run_eval  # noqa: E402


def test_run_all_preserves_order_and_isolates_errors(monkeypatch):
    monkeypatch.setenv("EVAL_WORKERS", "1")  # in-process: monkeypatch is visible, no spawn boundary

    def fake_run_one(entry: dict) -> dict:
        if entry["id"] == "boom":
            raise ValueError("kaboom")
        return {"id": entry["id"], "ok": True}

    monkeypatch.setattr(run_eval, "_run_one", fake_run_one)
    entries = [{"id": f"f{i}", "accession": f"acc{i}"} for i in range(6)]
    entries[2] = {"id": "boom", "accession": "accX"}  # one filing fails mid-batch

    rows = run_eval._run_all(entries)

    assert [r["id"] for r in rows] == [e["id"] for e in entries]          # order preserved
    assert "error" in rows[2] and "kaboom" in rows[2]["error"]            # failure isolated to its row
    assert all("error" not in r for i, r in enumerate(rows) if i != 2)    # other filings unaffected
