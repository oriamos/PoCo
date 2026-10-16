"""The shipped fine-tuned model: verified atomic download, repeat installs, registry integration, default selection.

A local HTTP server stands in for the GitHub Release; the pinned checksums are replaced by those of small fake files."""
import hashlib
import importlib.util
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import numpy as np
import pytest
from engines_fakes import FakeSpotiflow
from test_engines_spotiflow_adapter import call
from test_ml_registry import add_ft

from polony_app.engines import SpotiflowEngine
from polony_app.ml import bundled_model as bm
from polony_app.ml.app_model import resolve_for_detection
from polony_app.ml.common import MLError, models_dir
from polony_app.ml.registry import Registry

FAKE = {"best.pt": b"fake-weights" * 100, "config.yaml": b"fake: true\n", "thresholds.yaml": b"prob_thresh_best:\n- 0.3\n",
        "train_config.yaml": b"epochs: 1\n"}
REPO = Path(__file__).resolve().parents[2]


class Release:
    """Serves FAKE; ``mode`` injects faults: 'ok', 'corrupt' (wrong bytes), 'truncate' (short body), 'flaky' (first request fails)."""

    def __init__(self, files=FAKE):
        self.files, self.mode, self.hits, self.fail_next = files, "ok", [], 0
        outer = self

        class H(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def do_GET(self):
                name = self.path.rsplit("/", 1)[-1]
                outer.hits.append(name)
                if name not in outer.files:
                    self.send_error(404)
                    return
                body = outer.files[name]
                if outer.fail_next > 0:
                    outer.fail_next -= 1
                    self.send_error(503)
                    return
                if outer.mode == "corrupt" and name == "best.pt":
                    body = b"X" * len(body)
                self.send_response(200)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                if outer.mode == "truncate" and name == "best.pt":
                    self.wfile.write(body[: len(body) // 2])
                    self.wfile.flush()
                    self.close_connection = True
                    return
                self.wfile.write(body)

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), H)
        self.url = f"http://127.0.0.1:{self.server.server_address[1]}/rel"
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def close(self):
        self.server.shutdown()
        self.server.server_close()


@pytest.fixture
def rel(monkeypatch):
    monkeypatch.setattr(bm, "FILES", {n: (hashlib.sha256(b).hexdigest(), len(b)) for n, b in FAKE.items()})
    monkeypatch.delenv("POLONY_BUNDLED_MODEL", raising=False)
    monkeypatch.delenv("POLONY_MODEL_BASE_URL", raising=False)
    r = Release()
    yield r
    r.close()


def leftovers(folder):
    return sorted(p.name for p in folder.iterdir() if p.name.endswith(".part")) if folder.exists() else []


def test_pinned_values_match_the_release_manifest():
    m = json.loads((REPO / "model-release" / "model.json").read_text())
    assert m["id"] == bm.MODEL_ID and bm.RELEASE_TAG == f"model-{m['id']}"
    assert {n: (f["sha256"], f["bytes"]) for n, f in m["files"].items()} == bm.FILES
    assert m["inference_config"]["downscale"] == bm.INFERENCE_CONFIG["downscale"] == 4
    assert m["inference_config"]["normaliser"] == bm.INFERENCE_CONFIG["normaliser"] == "valid_unsaturated"
    assert m["inference_config"]["prob_thresh"] == 0.3
    assert bm.FILES["best.pt"][0] == "8edc09e3de3bb9da156930cd85f1d054daf6a52b937091b87fd08f0e063061fc"
    assert bm.BASE_URL.startswith("https://github.com/oriamos/poco/releases/download/")        # not the historical repository


def test_fresh_install_downloads_verifies_registers_and_activates(tmp_path, rel):
    res = bm.install_bundled(tmp_path, base_url=rel.url)
    assert res["status"] == "installed" and res["active"] == bm.MODEL_ID and res["activated"] and res["registered"]
    folder = models_dir(tmp_path) / bm.MODEL_ID
    for n, b in FAKE.items():
        assert (folder / n).read_bytes() == b
    assert leftovers(folder) == []
    reg = Registry(tmp_path)
    e = reg.get(bm.MODEL_ID)
    assert (e["origin"], e["status"], e["kind"], e["base"]) == ("bundled", "active", "finetuned", "general")
    assert e["inference_config"] == {"downscale": 4, "normaliser": "valid_unsaturated"}
    assert e["evaluations"] == [] and e["weights_sha256"] == hashlib.sha256(FAKE["best.pt"]).hexdigest()
    assert "Ori Amos" in e["distribution_approval"] and e["source"]["commit"] == "8e95882a7a3457bca86fe665289cc6ff49e2821b"
    ev = reg.load()["log"][-1]
    assert ev["event"] == "register_bundled" and ev["activated"] is True                    # auditable, not a silent promote


def test_repeat_install_reuses_verified_files(tmp_path, rel):
    bm.install_bundled(tmp_path, base_url=rel.url)
    n = len(rel.hits)
    before = Registry(tmp_path).path.read_text()
    res = bm.install_bundled(tmp_path, base_url=rel.url)
    assert res["status"] == "reused" and len(rel.hits) == n                                  # nothing downloaded
    assert Registry(tmp_path).path.read_text() == before                                     # registry untouched


def test_a_modified_file_on_disk_is_replaced(tmp_path, rel):
    bm.install_bundled(tmp_path, base_url=rel.url)
    w = models_dir(tmp_path) / bm.MODEL_ID / "best.pt"
    w.write_bytes(b"damaged")
    res = bm.install_bundled(tmp_path, base_url=rel.url)
    assert res["status"] == "installed" and w.read_bytes() == FAKE["best.pt"]


def test_corrupt_download_is_rejected_and_nothing_is_registered(tmp_path, rel):
    rel.mode = "corrupt"
    res = bm.install_bundled(tmp_path, base_url=rel.url)
    folder = models_dir(tmp_path) / bm.MODEL_ID
    assert res["status"] == "failed" and "SHA-256" in res["message"]
    assert not (folder / "best.pt").exists() and leftovers(folder) == []
    assert Registry(tmp_path).list() == [] and Registry(tmp_path).active_id() is None


def test_truncated_download_is_rejected_then_a_retry_succeeds(tmp_path, rel):
    rel.mode = "truncate"
    res = bm.install_bundled(tmp_path, base_url=rel.url)
    folder = models_dir(tmp_path) / bm.MODEL_ID
    assert res["status"] == "failed" and not (folder / "best.pt").exists() and leftovers(folder) == []
    assert Registry(tmp_path).list() == []
    rel.mode = "ok"
    res = bm.install_bundled(tmp_path, base_url=rel.url)
    assert res["status"] == "installed" and (folder / "best.pt").read_bytes() == FAKE["best.pt"]


def test_an_interrupted_server_is_retried_inside_one_install(tmp_path, rel):
    rel.fail_next = 2                                                                         # two 503s, then fine
    assert bm.install_bundled(tmp_path, base_url=rel.url)["status"] == "installed"


def test_unreachable_server_fails_without_touching_anything(tmp_path, monkeypatch):
    monkeypatch.setenv("POLONY_MODEL_BASE_URL", "http://127.0.0.1:9/none")
    res = bm.install_bundled(tmp_path)
    assert res["status"] == "failed" and Registry(tmp_path).list() == []


def test_opt_out(tmp_path, rel, monkeypatch):
    monkeypatch.setenv("POLONY_BUNDLED_MODEL", "0")
    assert bm.install_bundled(tmp_path, base_url=rel.url)["status"] == "skipped" and rel.hits == []


def test_an_existing_active_model_and_user_models_are_preserved(tmp_path, rel):
    reg = Registry(tmp_path)
    add_ft(reg, tmp_path, "mine-1")
    reg.promote("mine-1", force=True, reason="my choice")
    before = reg.get("mine-1")
    res = bm.install_bundled(tmp_path, base_url=rel.url)
    assert res["status"] == "installed" and res["active"] == "mine-1" and not res["activated"]
    assert reg.active_id() == "mine-1" and reg.get("mine-1") == before
    assert reg.get(bm.MODEL_ID)["status"] == "candidate"                                      # available by id, not the default
    assert resolve_for_detection({"model_name": bm.MODEL_ID}, tmp_path)[1]                    # can still be chosen explicitly


def test_a_rollback_is_not_undone_by_a_repeat_install(tmp_path, rel):
    bm.install_bundled(tmp_path, base_url=rel.url)
    Registry(tmp_path).rollback()                                                             # the user returns to pretrained
    res = bm.install_bundled(tmp_path, base_url=rel.url)
    assert res["active"] is None and res["status"] == "reused" and not res["activated"]
    assert resolve_for_detection({"model_name": "active"}, tmp_path)[0]["model_name"] == "general"


def test_promotion_safeguards_still_apply_to_a_bundled_candidate(tmp_path, rel):
    add_ft(Registry(tmp_path), tmp_path, "mine-1")
    Registry(tmp_path).promote("mine-1", force=True, reason="x")
    bm.install_bundled(tmp_path, base_url=rel.url)                                            # registered as candidate
    with pytest.raises(MLError):                                                              # no invented evidence
        Registry(tmp_path).promote(bm.MODEL_ID, lock_sha256="a" * 64)


def test_an_entry_with_different_weights_is_never_overwritten(tmp_path, rel):
    add_ft(Registry(tmp_path), tmp_path, bm.MODEL_ID, weights=b"someone else's model")
    (models_dir(tmp_path) / bm.MODEL_ID / "best.pt").unlink()
    res = bm.install_bundled(tmp_path, base_url=rel.url)
    assert res["status"] == "failed" and "different weights" in res["message"]


def test_fresh_install_makes_the_shipped_model_the_default_for_detection(tmp_path, rel, monkeypatch):
    fs = FakeSpotiflow(monkeypatch, tmp_path / "cache")
    data = tmp_path / "data"
    bm.install_bundled(data, base_url=rel.url)
    p, load_from, notes = resolve_for_detection({"model_name": "active"}, data)
    assert (p["model_name"], p["downscale"], p["normalizer"]) == (bm.MODEL_ID, 4, "valid_unsaturated")
    assert load_from == str(models_dir(data) / bm.MODEL_ID)
    img = np.random.default_rng(0).integers(500, 3000, (256, 256)).astype(np.uint16)
    res = call(SpotiflowEngine(cache_dir=fs.cache_dir, data_dir=data), img, params={"model_name": "active"})
    assert fs.loads[-1]["path"] == load_from and res.run.model_name == bm.MODEL_ID and res.run.params["downscale"] == 4
    # the pretrained model stays available by name
    res2 = call(SpotiflowEngine(cache_dir=fs.cache_dir, data_dir=data), img, params={"model_name": "general"})
    assert res2.run.model_name == "general"


def test_the_installer_script_runs_the_same_code(tmp_path, rel, monkeypatch):
    monkeypatch.setenv("POLONY_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("POLONY_HOME", str(tmp_path / "home"))
    monkeypatch.setenv("POLONY_MODEL_BASE_URL", rel.url)
    spec = importlib.util.spec_from_file_location("ai_extra_under_test", REPO / "install" / "ai_extra.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.cmd_model() == 0
    assert Registry(tmp_path / "data").active_id() == bm.MODEL_ID
    assert mod.cmd_model() == 0 and len(rel.hits) == len(FAKE)                                # second run downloads nothing
    rel.close()
    monkeypatch.setenv("POLONY_MODEL_BASE_URL", "http://127.0.0.1:9/none")
    (tmp_path / "data2").mkdir()
    monkeypatch.setenv("POLONY_DATA_DIR", str(tmp_path / "data2"))
    assert mod.cmd_model() == 1                                                               # failure is reported, not raised
