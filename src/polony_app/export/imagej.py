"""ImageJ-native export of a reviewed slide: `<name>_imagej.tif` + `<name>_rois.zip`.

The TIFF holds the RAW red and green planes (2-channel ImageJ hyperstack) with the counted objects, the counting grid
and the per-field counts stored as an ImageJ *overlay*; the ZIP is the same ROIs as a RoiSet (ROI Manager > Open).
A reader without PoCo opens the TIFF in ImageJ/Fiji and sees exactly what was counted. Only counted objects are drawn
(same rule as the ringed `_labeled.tif`); uncertain, deleted and switched-off-field objects are not.
Coordinates: PoCo pixel centres are integers, ImageJ's frame puts a pixel centre at +0.5, hence the +0.5 shift.
"""
from __future__ import annotations

import os
import zipfile
from pathlib import Path

import numpy as np

from polony_app.schemas import Analysis, ObjectClass, RegionKind

_COLOR = {ObjectClass.red: (255, 140, 0), ObjectClass.green: (0, 255, 255), ObjectClass.yellow: (255, 255, 0)}
_GRID = (255, 255, 255)
_MAGENTA = (255, 0, 255)


def _argb(rgb: tuple[int, int, int]) -> bytes:
    return bytes([255, *rgb])


def build_rois(a: Analysis, selected: set[ObjectClass], per_field: dict[int, int], field_regions: dict) -> list:
    """ImageJ ROIs (roifile.ImagejRoi) for the counted objects, field outlines + count labels, exclusion regions."""
    from roifile import ROI_OPTIONS, ROI_SUBTYPE, ROI_TYPE, ImagejRoi

    h = 0.5
    rois: list = []

    def outline(poly, name, rgb):
        pts = np.asarray([(x + h, y + h) for x, y in poly], float)
        r = ImagejRoi.frompoints(pts, name=name)
        r.roitype = ROI_TYPE.POLYGON
        r.stroke_color = _argb(rgb)
        r.stroke_width = 1
        return r

    for reg in a.regions:
        if reg.kind == RegionKind.exclusion:
            rois.append(outline(reg.polygon, f"excluded {reg.name}", _MAGENTA))
    for f, reg in sorted(field_regions.items()):
        rois.append(outline(reg.polygon, f"field {f}", _GRID))
        x0 = min(p[0] for p in reg.polygon) + h
        y0 = min(p[1] for p in reg.polygon) + h
        size = max(14, int(min(abs(max(p[1] for p in reg.polygon) - min(p[1] for p in reg.polygon)), 400) // 8))
        t = ImagejRoi(roitype=ROI_TYPE.RECT, subtype=ROI_SUBTYPE.TEXT, left=int(x0) + 4, top=int(y0) + 2,
                      right=int(x0) + 4 + size * 5, bottom=int(y0) + 2 + size * 2, text=f"{f}: {per_field.get(f, 0)}",
                      text_size=size, name=f"count field {f}")
        t.stroke_color = _argb(_GRID)
        rois.append(t)
    in_field = {r.id: f for f, r in field_regions.items()}
    rad = 3.0
    counters: dict[tuple[int, str], int] = {}
    for o in a.objects:
        if o.deleted or o.region_id not in in_field or o.cls not in selected:
            continue
        f = in_field[o.region_id]
        k = counters[(f, o.cls.value)] = counters.get((f, o.cls.value), 0) + 1
        r = ImagejRoi(roitype=ROI_TYPE.OVAL, subtype=ROI_SUBTYPE.UNDEFINED, options=ROI_OPTIONS.SUB_PIXEL_RESOLUTION,
                      left=int(round(o.x + h - rad)), top=int(round(o.y + h - rad)),
                      right=int(round(o.x + h + rad)), bottom=int(round(o.y + h + rad)),
                      xd=o.x + h - rad, yd=o.y + h - rad, widthd=2 * rad, heightd=2 * rad,
                      name=f"{o.cls.value} F{f} #{k}")
        r.stroke_color = _argb(_COLOR[o.cls])
        r.stroke_width = 1
        rois.append(r)
    return rois


def write_imagej(path: Path, red: np.ndarray, green: np.ndarray, rois: list) -> None:
    """2-channel ImageJ TIFF (raw pixel values, dtype kept) with `rois` as overlay."""
    import tifffile

    stack = np.stack([red, green])
    tmp = path.with_name(path.name + f".tmp{os.getpid()}")
    try:
        tifffile.imwrite(tmp, stack, imagej=True, metadata={"axes": "CYX", "mode": "composite",
                         "Overlays": [r.tobytes() for r in rois]}, software="Polony Review")
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink()


def write_roiset(path: Path, rois: list) -> None:
    """RoiSet .zip (ImageJ ROI Manager format): one .roi per ROI, unique names."""
    tmp = path.with_name(path.name + f".tmp{os.getpid()}")
    try:
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
            for i, r in enumerate(rois, 1):
                z.writestr(f"{i:05d}-{r.name}.roi".replace("/", "_").replace("#", ""), r.tobytes())
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink()
