---
name: Scientific result (disputed count or unexpected detection)
about: A count, detection, or claim looks wrong
title: "[result] "
labels: scientific
---

> **Do not attach private lab images.** Do not attach TIFF scans, screenshots, CSV or Excel results, or provenance files
> from the laboratory. Describe the image in words instead, for example "a bright spot in the lower-left of field 12,
> about 3 pixels across". Maintainers cannot review private data through this issue.
>
> Use a synthetic example or the file in `resources/dataset_files/test` where you can.

## What looks wrong

Describe the count, detection, or claim that you think is incorrect or surprising.

## Type of data

- [ ] Synthetic example (describe how it was made)
- [ ] The example in `resources/dataset_files/test`
- [ ] Private laboratory data, described in words only (no file attached)

## Expected and observed

- Expected count or detection, and how you determined it:
- Observed count or detection:
- Tolerance used when comparing (native pixels), if any:

## Settings

- App version (see `pyproject.toml`, currently 0.3.3):
- Detector (Big-FISH, Spotiflow `general`, or a named model):
- Parameters changed from the defaults (list them):
- Downscale and normaliser, if known:
- Operating system:

## Evidence

Describe the evidence in words (for example, how many fields, how many slides, and how the reference marks were made).
Do not attach laboratory images.

## Scientific limits

Is this a single example, or a repeated pattern? How many slides, fields, or groups does it cover? Do not state accuracy
figures unless you have a documented test that supports them.
