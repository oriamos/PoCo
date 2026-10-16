"""The fine-tuned model that ships with PoCo: verified download from the model release and registration in the registry.

``install_bundled`` is what the AI installer calls (``install/ai_extra.py``); the installers for Windows, macOS and Linux
all go through it. It downloads the pinned files from the GitHub Release ``model-<id>`` of oriamos/poco, checks size and
SHA-256 against the values pinned below, and registers the model with ``Registry.register_bundled``.

* Downloads are atomic: a ``.part`` file is verified, then renamed. A truncated or modified download is deleted, never kept.
* A repeat install finds verified files and downloads nothing.
* Existing models, the active model and explicit user choices are never changed (see ``Registry.register_bundled``).
* ``POLONY_BUNDLED_MODEL=0`` skips it; ``POLONY_MODEL_BASE_URL`` replaces the download folder URL (mirrors, tests).
"""
from __future__ import annotations

import os
import urllib.request
from pathlib import Path
from typing import Callable, Optional

from .common import MLError, models_dir, sha256_file
from .registry import Registry

MODEL_ID = "ft-7e4c89cb-8edc09e3"
RELEASE_TAG = f"model-{MODEL_ID}"
BASE_URL = f"https://github.com/oriamos/poco/releases/download/{RELEASE_TAG}"
WEIGHTS = "best.pt"
FILES: dict[str, tuple[str, int]] = {       # name -> (sha256, bytes); the trust root of the download
    "best.pt": ("8edc09e3de3bb9da156930cd85f1d054daf6a52b937091b87fd08f0e063061fc", 47406478),
    "config.yaml": ("9c04e562ef8dc1ca4167d032506533051638ef15cbb55e3c5bb58e3baa2164e5", 416),
    "thresholds.yaml": ("f63b656f20f5c45143686c34d04f20a08c078f6e5b88ad2e0f40aab0de24f04f", 48),
    "train_config.yaml": ("e26936d84f7ef91d4c7b66fffca560c97cf7205dc42c0637d03ff45b4115459c", 303),
}
INFERENCE_CONFIG = {"downscale": 4, "normaliser": "valid_unsaturated"}
SOURCE = {"repository": "oriamos/polony-counting", "commit": "8e95882a7a3457bca86fe665289cc6ff49e2821b",
          "path": f"artifacts/{MODEL_ID}", "release": f"https://github.com/oriamos/poco/releases/tag/{RELEASE_TAG}"}
APPROVAL = ("The laboratory approved distribution of this model to PoCo users; recorded from confirmation given by Ori Amos. "
            "No approver name or date beyond that was recorded.")

Progress = Callable[[str], None]


def _say(progress: Optional[Progress], msg: str) -> None:
    if progress:
        progress(msg)


def is_verified(path: Path, sha256: str, size: int) -> bool:
    try:
        return path.is_file() and path.stat().st_size == size and sha256_file(path) == sha256
    except OSError:
        return False


def download_verified(url: str, dest: Path, sha256: str, size: int, *, timeout: float = 60.0, retries: int = 3) -> None:
    """Download ``url`` to ``dest`` atomically; ``dest`` exists afterwards only if size and SHA-256 match."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_name(f".{dest.name}.{os.getpid()}.part")
    last: Optional[Exception] = None
    for _ in range(max(1, retries)):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "PoCo-installer"}), timeout=timeout) as r, \
                    open(part, "wb") as f:
                while True:
                    b = r.read(1 << 20)
                    if not b:
                        break
                    f.write(b)
            if part.stat().st_size != size:
                raise MLError(f"{dest.name}: downloaded {part.stat().st_size} bytes, expected {size} (truncated or wrong file)")
            got = sha256_file(part)
            if got != sha256:
                raise MLError(f"{dest.name}: SHA-256 {got} does not match the pinned {sha256}")
            os.replace(part, dest)
            return
        except Exception as exc:  # network error, truncated body, wrong content: try again, then report
            last = exc
        finally:
            try:
                part.unlink()
            except OSError:
                pass
    raise MLError(f"could not download {dest.name} from {url}: {last}")


def fetch_files(folder: Path, base_url: str = BASE_URL, progress: Optional[Progress] = None) -> bool:
    """Make ``folder`` hold every pinned file, verified. Returns True when something was downloaded."""
    downloaded = False
    for name, (sha, size) in FILES.items():
        target = folder / name
        if is_verified(target, sha, size):
            continue
        if target.exists():
            _say(progress, f"{name} on disk does not match the pinned checksum; replacing it")
        _say(progress, f"downloading {name} ({size / 1e6:.1f} MB)" if size > 1e6 else f"downloading {name}")
        download_verified(f"{base_url.rstrip('/')}/{name}", target, sha, size)
        downloaded = True
    return downloaded


def install_bundled(data_dir: str | Path, *, base_url: Optional[str] = None, progress: Optional[Progress] = None) -> dict:
    """Download (if needed), verify and register the shipped model. Never raises for network problems: returns a result dict

    ``{"status": "installed" | "reused" | "skipped" | "failed", "model_id", "active", "message"}``."""
    if os.environ.get("POLONY_BUNDLED_MODEL", "1").strip().lower() in ("0", "no", "false", "off"):
        return {"status": "skipped", "model_id": MODEL_ID, "active": None, "message": "POLONY_BUNDLED_MODEL=0: not installing the shipped model"}
    base = base_url or os.environ.get("POLONY_MODEL_BASE_URL") or BASE_URL
    folder = models_dir(data_dir) / MODEL_ID
    try:
        downloaded = fetch_files(folder, base, progress)
        reg = Registry(data_dir)
        res = reg.register_bundled(
            MODEL_ID, base="general", weights_file=WEIGHTS, weights_sha256=FILES[WEIGHTS][0], artifact=MODEL_ID,
            artifact_files={n: sha for n, (sha, _) in FILES.items()}, inference_config=dict(INFERENCE_CONFIG),
            source=SOURCE, approval=APPROVAL)
        active = reg.active_id()
    except (MLError, OSError) as exc:
        return {"status": "failed", "model_id": MODEL_ID, "active": None, "message": str(exc)}
    status = "installed" if (downloaded or res["registered"]) else "reused"
    default = "it is the default model" if active == MODEL_ID else "the existing default model was kept"
    how = "downloaded and verified" if downloaded else "already on disk and verified"
    return {"status": status, "model_id": MODEL_ID, "active": active, "registered": res["registered"],
            "activated": res["activated"], "message": f"{MODEL_ID} {how}; {default}"}
