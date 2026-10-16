"""Real-inference smoke test of the shipped fine-tuned model in an installed PoCo (AI extra installed).

Run with the installed venv's python after the AI install, from the app folder:  python install/ci/smoke_model.py [slide.tif]
Checks: the registry's active model is the shipped one, its weights match the pinned checksum, a default ("active")
Spotiflow detection loads those weights and runs with downscale 4, normaliser valid_unsaturated and threshold 0.3,
finds spots on the synthetic demo slide, and the run record names the model. Exit code 0 = all true."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import tifffile

from polony_app.engines import SpotiflowEngine
from polony_app.launcher import data_dir
from polony_app.ml import bundled_model as bm
from polony_app.ml.common import sha256_file
from polony_app.ml.registry import Registry
from polony_app.schemas import SpotiflowParams


def main(argv: list[str]) -> int:
    dd = data_dir()
    reg = Registry(dd)
    assert reg.active_id() == bm.MODEL_ID, f"active model is {reg.active_id()!r}, expected {bm.MODEL_ID}"
    e = reg.get(bm.MODEL_ID)
    w = dd / "models" / bm.MODEL_ID / "best.pt"
    assert sha256_file(w) == bm.FILES["best.pt"][0] == e["weights_sha256"], "weights checksum differs from the pinned value"
    slide = Path(argv[0]) if argv else Path(__file__).resolve().parents[2] / "resources" / "dataset_files" / "test" / "test_img.tif"
    img = tifffile.imread(slide)[0]
    valid = np.zeros(img.shape, bool)
    valid[300:1100, 300:1100] = True
    assert SpotiflowParams().model_name == "active"
    res = SpotiflowEngine(data_dir=dd).detect_page(img, analysis_id="smoke", page=0, channel_role="red", valid_mask=valid,
                                                   params={"model_name": "active"}, image_sha256={})
    r = res.run
    print(f"status={r.status} model={r.model_name} detections={len(res.detections)} device={r.device} "
          f"downscale={r.params.get('downscale')} normalizer={r.params.get('normalizer')} threshold={r.params.get('prob_thresh_used')} "
          f"weights={(r.model_checksum or '')[:12]}")
    assert r.status == "ok", r.status
    assert r.model_name == bm.MODEL_ID
    assert r.params.get("downscale") == 4 and r.params.get("normalizer") == "valid_unsaturated"
    assert abs(float(r.params.get("prob_thresh_used")) - 0.3) < 1e-6, r.params.get("prob_thresh_used")
    assert r.model_checksum and r.model_checksum.startswith(bm.FILES["best.pt"][0][:12]) or r.model_checksum == bm.FILES["best.pt"][0]
    assert len(res.detections) > 0, "no detections on the demo slide"
    print("smoke OK: the shipped fine-tuned model is the default and runs with its own configuration")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
