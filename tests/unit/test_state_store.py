from pathlib import Path

from apps.backend import state_store


def test_save_and_load_state(tmp_path, monkeypatch):
    path = tmp_path / "runtime_status.json"
    monkeypatch.setattr(state_store, "STATE_PATH", path)

    payload = {"repos": {"demo": {"status": "healthy"}}, "actions": [{"repo": "demo"}]}
    state_store.save_state(payload)

    loaded = state_store.load_state()
    assert loaded["repos"]["demo"]["status"] == "healthy"
