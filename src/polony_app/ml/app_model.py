"""Which Spotiflow model the app detection uses.

``SpotiflowParams.model_name`` may be

* ``"active"``      the promoted model of the model registry, or the default pretrained model when none is promoted;
* a registry id     a fine-tuned candidate (or retired model) named explicitly;
* anything else     an official pretrained name or a model folder, used as before.

A fine-tuned model is run with the downscale and normaliser it was trained with; its own saved threshold applies when
``prob_thresh`` is None. The run record names the model by its registry id and keeps its weights checksum (the model folder is
recorded in the run parameters, as for every model).
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

ACTIVE = "active"
_NORMALISERS = ("auto", "none", "valid_unsaturated")


class ModelResolutionError(Exception):
    """The requested registry model cannot be used (unknown, files missing or modified)."""


def resolve_for_detection(params: dict, data_dir: Optional[str | Path]) -> tuple[dict, Optional[str], list[str]]:
    """Return ``(params, load_from, notes)``.

    ``params`` keeps the requested name resolved to a registry id or an official name (what is recorded). ``load_from`` is the
    model folder to load when it differs from the name (a registry model), else None."""
    from .registry import DEFAULT_PRETRAINED, MLError, resolve_model

    out = dict(params)
    name = str(out.get("model_name") or ACTIVE)
    if data_dir is None:
        out["model_name"] = DEFAULT_PRETRAINED if name == ACTIVE else name
        return out, None, []
    try:
        ref = resolve_model(name, data_dir)
    except MLError as exc:
        raise ModelResolutionError(str(exc)) from exc
    if ref.kind == "pretrained":
        notes = [f"no promoted model in the registry: using the pretrained '{ref.name}'"] if name == ACTIVE else []
        out["model_name"] = ref.name
        return out, None, notes
    cfg = ref.inference_config or {}
    out["model_name"] = ref.registry_id or ref.name
    if cfg.get("downscale"):
        out["downscale"] = int(cfg["downscale"])
    if cfg.get("normaliser") in _NORMALISERS:
        out["normalizer"] = cfg["normaliser"]
    elif cfg.get("normaliser"):
        out["normalizer"] = "auto"          # models trained before page-level normalisation (legacy per-crop)
    notes = [f"model: fine-tuned '{out['model_name']}' (registry status: {ref.status or 'unknown'}), weights sha256 "
             f"{(ref.weights_sha256 or '?')[:12]}; run with the downscale {out.get('downscale')} and normaliser "
             f"{out.get('normalizer')} it was trained with"]
    return out, str(ref.path), notes
