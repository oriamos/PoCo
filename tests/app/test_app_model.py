"""App detection uses the promoted (or a named) registry model; without one it is the pretrained 'general' as before."""
import numpy as np
import pytest
from engines_fakes import FakeSpotiflow
from test_engines_spotiflow_adapter import call
from test_ml_registry import add_ft

from polony_app.engines import SpotiflowEngine
from polony_app.ml.app_model import ModelResolutionError, resolve_for_detection
from polony_app.ml.registry import Registry
from polony_app.schemas import SpotiflowParams

CFG4 = {"downscale": 4, "normaliser": "valid_unsaturated"}


def test_the_default_model_name_is_active():
    assert SpotiflowParams().model_name == "active"


def test_active_without_a_promoted_model_is_the_pretrained_default(tmp_path):
    p, load_from, notes = resolve_for_detection({"model_name": "active", "downscale": 1}, tmp_path)
    assert p["model_name"] == "general" and load_from is None and "no promoted model" in notes[0]
    p, load_from, notes = resolve_for_detection({"model_name": "hybiss"}, tmp_path)      # an official name passes through
    assert p["model_name"] == "hybiss" and load_from is None and notes == []
    p, _, _ = resolve_for_detection({"model_name": "active"}, None)                      # no data folder: the default
    assert p["model_name"] == "general"


def test_a_promoted_model_is_resolved_with_its_own_configuration(tmp_path):
    reg = Registry(tmp_path)
    d = add_ft(reg, tmp_path, "ft-1", config=CFG4)
    reg.promote("ft-1", force=True, reason="test")
    p, load_from, notes = resolve_for_detection({"model_name": "active", "downscale": 1, "normalizer": "auto"}, tmp_path)
    assert (p["model_name"], p["downscale"], p["normalizer"]) == ("ft-1", 4, "valid_unsaturated")
    assert load_from == str(d) and "ft-1" in notes[0] and "downscale 4" in notes[0]
    assert str(tmp_path) not in p["model_name"]                       # the model is named by its registry id


def test_a_candidate_can_be_named_but_is_not_the_default(tmp_path):
    reg = Registry(tmp_path)
    add_ft(reg, tmp_path, "ft-1", config=CFG4)
    assert resolve_for_detection({"model_name": "active"}, tmp_path)[0]["model_name"] == "general"
    p, load_from, _ = resolve_for_detection({"model_name": "ft-1"}, tmp_path)
    assert p["model_name"] == "ft-1" and load_from


def test_modified_or_missing_weights_are_refused(tmp_path):
    reg = Registry(tmp_path)
    d = add_ft(reg, tmp_path, "ft-1", config=CFG4)
    (d / "best.pt").write_bytes(b"other")
    with pytest.raises(ModelResolutionError, match="do not match"):
        resolve_for_detection({"model_name": "ft-1"}, tmp_path)


def test_the_engine_runs_the_promoted_model_and_records_its_id(monkeypatch, tmp_path):
    fs = FakeSpotiflow(monkeypatch, tmp_path / "cache")
    data = tmp_path / "data"
    reg = Registry(data)
    d = add_ft(reg, data, "ft-1", config=CFG4)
    (d / "config.yaml").write_text("fake: true\n")                  # a real model folder has its config next to the weights
    reg.promote("ft-1", force=True, reason="test")
    img = np.random.default_rng(0).integers(500, 3000, (256, 256)).astype(np.uint16)
    eng = SpotiflowEngine(cache_dir=fs.cache_dir, data_dir=data)
    res = call(eng, img, params={"model_name": "active"})
    assert fs.loads[-1]["path"] == str(d)                               # the registry folder was loaded
    r = res.run
    assert r.model_name == "ft-1" and r.params["model_name"] == "ft-1" and r.params["downscale"] == 4
    assert any("fine-tuned 'ft-1'" in n for n in r.notes)
    # with no promoted model the same request uses the pretrained 'general'
    other = tmp_path / "empty"
    fs2 = FakeSpotiflow(monkeypatch, tmp_path / "cache2")
    res2 = call(SpotiflowEngine(cache_dir=fs2.cache_dir, data_dir=other), img, params={"model_name": "active"})
    assert res2.run.model_name == "general" and any("no promoted model" in n for n in res2.run.notes)


def test_a_broken_registry_model_is_an_engine_error_not_a_crash(monkeypatch, tmp_path):
    from polony_app.engines.base import EngineError
    fs = FakeSpotiflow(monkeypatch, tmp_path / "cache")
    data = tmp_path / "data"
    reg = Registry(data)
    d = add_ft(reg, data, "ft-1", config=CFG4)
    (d / "best.pt").write_bytes(b"tampered")
    with pytest.raises(EngineError, match="do not match"):
        call(SpotiflowEngine(cache_dir=fs.cache_dir, data_dir=data), np.full((64, 64), 5, np.uint16), params={"model_name": "ft-1"})


def test_api_detection_uses_the_promoted_model_by_default(monkeypatch, tmp_path):
    """Promote -> a default hybrid detection through the API runs the registry model and records its id."""
    pytest.importorskip("bigfish")
    from fakes import counting, rect, wait_job, write_two_channel_tiff
    from fastapi.testclient import TestClient

    from polony_app.api.main import create_app

    fs = FakeSpotiflow(monkeypatch, tmp_path / "cache")
    monkeypatch.setenv("POLONY_MODEL_DIR", str(fs.cache_dir))
    data = tmp_path / "data"
    reg = Registry(data)
    d = add_ft(reg, data, "ft-1", config=CFG4)
    (d / "config.yaml").write_text("fake: true\n")
    reg.promote("ft-1", force=True, reason="test")
    write_two_channel_tiff(tmp_path / "s.tif")
    with TestClient(create_app(data)) as c:
        with open(tmp_path / "s.tif", "rb") as f:
            aid = c.post("/api/analyses", files=[("files", ("s.tif", f, "image/tiff"))]).json()["id"]
        c.put(f"/api/analyses/{aid}/channels", json={"mapping": [{"index": 0, "role": "red"}, {"index": 1, "role": "green"}]})
        c.put(f"/api/analyses/{aid}/regions", json={"regions": [counting("c1", rect(2, 2, 157, 117)).model_dump(mode="json")]})
        models = next(e for e in c.get("/api/engines").json() if e["name"] == "spotiflow")["models"]
        assert models[0]["name"] == "active" and "ft-1" in models[0]["label"] and any(m["name"] == "ft-1" for m in models)
        j = wait_job(c, c.post(f"/api/analyses/{aid}/detect", json={"engine": "spotiflow"}).json()["id"], 120)
        assert j["status"] == "done", j
        runs = [r for r in c.get(f"/api/analyses/{aid}/engine-runs").json() if r["engine"] == "spotiflow"]
        assert runs and {r["model_name"] for r in runs} == {"ft-1"}
        assert {r["params"]["downscale"] for r in runs} == {4}
    assert any(load["path"] == str(d) for load in fs.loads)
