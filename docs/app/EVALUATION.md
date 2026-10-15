# Evaluation of detection configurations

> **About `test_img`.** Numbers quoted here for `test_img` come from an earlier real laboratory image that is no longer distributed. The `test_img.tif` in this repository is a synthetic stand-in (`resources/dataset_files/test/make_test_img.py`), so they cannot be reproduced with it. See [../STATUS_AND_RESULTS.md](../STATUS_AND_RESULTS.md), [../REPRODUCIBILITY.md](../REPRODUCIBILITY.md).

Write a Markdown report and a JSON file next to it:

```bash
python -m polony_app.ml evaluate --predictions <analysis ids> --reference analysis|roi [--tolerance 10] [--out report.md]
```

Model checkpoints are scored on the locked test crops with `eval-model` ([FINE_TUNING.md](FINE_TUNING.md)).

The reference is either the **final human-reviewed points** (`analysis`, fully reviewed regions only) or the **researcher's reference marks** embedded in the TIFF (`roi`, fields with marks on that page; the file cannot distinguish "counted zero" from "not counted", so fields without marks are not scored). Neither is ground truth.

## How points are compared
Per TIFF page, predictions and reference points closer than the tolerance are matched **one-to-one** (Hungarian assignment: maximum pairs first, then minimum total distance), **once over the union of the page's evaluated fields**. Each pair is credited to the field of its reference point, so a pair straddling a field border is not lost. Page index is the TIFF page; colour is shown only when the channel mapping is confirmed.

**Tolerance.** Default **10 px**; **5, 10 and 15 px are always reported side by side**. A 5 px radius mostly measures the annotator's click scatter (two people marking the same polony differ by about that much), not detection. Read the three columns together and prefer the one matching the physical spot size.

| metric | meaning |
|---|---|
| precision (**vs this annotator's marks**) | share of predicted points with a reference partner. A real polony the annotator did not mark is a false positive, so this is a lower bound on true precision |
| recall | share of reference points found |
| F1 | harmonic mean of the two |
| mean matching distance | average pixel distance of matched pairs (localisation quality) |
| per-field count MAE | average of \|predicted − reference count\| over fields |
| count bias | average of (predicted − reference) over fields; > 0 over-counts |
| OLS slope and intercept | least-squares line predicted = intercept + slope × reference over fields (slope 1, intercept 0 = no systematic error). A line through the origin is not used: it hides offsets (predicted = reference + 3 would show slope ≈ 1.1) |
| mean bias and limits of agreement | Bland–Altman, per slide: mean of (predicted − reference) and bias ± 1.96·SD |
| Pearson r (within slide) | correlation of per-field counts **inside one slide**; per slide, with its median |
| pooled Pearson r | over several slides, labelled **between-slide (not accuracy)**: slides differ in density, so it is high even when counts of fields within one slide are unrelated to the reference (synthetic example: within-slide r ≈ 0, pooled 0.96; real Spotiflow: pooled 0.95, within-slide mean 0.65) |
| false positives / false negatives per field | average unmatched predictions / unmatched reference points |
| % candidates needing review | candidates with a review reason or an engine disagreement |
| agreement / Big-FISH-only / Spotiflow-only acceptance | share of those candidates the reviewer kept |
| human-added rate | human-added points ÷ all final points (what the engines missed) |
| review time per field | estimated from action-log timestamps (gaps over 120 s count as breaks); empty when not measurable |

`undefined` values (e.g. precision with no predictions) are shown as `-`, never 0.

## Configurations
`bigfish_default`, `bigfish_sensitive` (threshold_scale 0.5), `spotiflow_pretrained`, `spotiflow_finetuned` (model name is a registry id; see below), `agreement_subset` (candidates both engines found), `union_before_review` (all candidates before any human action), `final_human_reviewed` (against `roi` only; against `analysis` it would equal the reference). Engine-based configurations read the stored raw detections of the analysis' engine runs; if the store has none, the config is reported as unavailable with the reason.

**Spotiflow runs are not one configuration.** Each distinct (downscale, probability threshold actually used, normaliser, model checksum, crop-to-valid / crop box) is its own configuration, e.g. `spotiflow_pretrained [downscale=4, thr=0.45, normaliser=valid_unsaturated, model=ab12cd34]`. All configurations found are listed ("Engine configurations found"); none is preferred or merged. Only runs with an *identical* configuration on the same page collapse to the most recent one, with a warning. `--predictions id:run1,run2` restricts the runs considered.

## Reading the report
* Sections: **per TIFF page** (always), a pooled row (only over pages with enough events, naming the pages it contains and the sparse ones it leaves out), then by slide, field, channel, spot radius and model version.
* Pages are never merged silently: a sparse (e.g. green) page is reported on its own, **not** added into the red totals.
* **preliminary**: set automatically with fewer than 30 fields, fewer than 30 reference events on the page, or only one annotator/review session (reviewer bias unmeasurable). Use such numbers for orientation, not claims. The reasons are listed under each table.
* Compare configurations on the *same* analyses and reference only. A better F1 against human-reviewed points can partly be agreement with the reviewer's habits (e.g. accepting what an engine proposed).
* **Count agreement** is reported per slide and page (OLS slope, intercept, bias, limits of agreement, within-slide r) with the median per-slide r; the pooled r is labelled between-slide.
* **Annotation completeness.** When raw detections are available, the report adds per slide how many raw proposals inside the reviewed fields the annotator left unmarked and how many are *bright* (score at least the lower quartile of the confirmed proposals). Some are real polonies nobody marked, so precision is a lower bound; dataset manifests carry the same counts.
* **Model score.** The Spotiflow score is a heatmap value at the peak, **not a calibrated probability**: against reviewer decisions the expected calibration error is about 0.27–0.30 and the AUC about 0.55–0.64. It is called "model score" everywhere and must not be used as a confidence statement.
* No numbers from earlier validation runs are built into the tool; every figure comes from the analyses you pass in.
