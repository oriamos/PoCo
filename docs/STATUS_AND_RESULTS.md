# Status and results

This is the one place that states what has been measured, on what data, and what is connected in the application. Other
documents go into more detail; where they disagree with this page, fix the other document.

Three different things are described here. Do not combine them.

| | What it is | Data | Status |
|---|---|---|---|
| **A** | Exploratory evaluation of pretrained detectors on eight slides | 8 real slides, one annotator | preliminary; not validation |
| **B** | Fine-tuning run on the saved historical data | ~13,200 crops from the historical ImageJ TIFFs; saved researcher marks | candidate model; not in the application |
| **C** | Application integration | the React app and the model registry | promotion is not connected to detection |

All results are agreement with saved researcher marks. None is a measure of accuracy on new laboratory images, and none shows that
the software's counts are correct for a given slide.

## A. The eight-slide exploratory evaluation

Details: [app/ALL_SLIDES_EVAL.md](app/ALL_SLIDES_EVAL.md) and [app/EVALUATION.md](app/EVALUATION.md).

* Eight real two-channel slides, marked by one annotator.
* Marks may be incomplete. An unmarked spot is not the same as a verified absence, so precision and recall are only partly meaningful.
* Results vary a lot from slide to slide: sparse slides give low precision for both detectors.
* Earlier fine-tuning experiments on two or three slides did not show a reliable improvement over the pretrained Spotiflow model at the same
  threshold (F1 changed by −0.03 to +0.02). See [app/FINE_TUNING.md](app/FINE_TUNING.md).
* The Spotiflow columns in the all-slides table are marked as superseded in that document; use its per-threshold tables.
* These are exploratory results. They are not general validation.
* Numbers quoted for `test_img` in older documents belong to an earlier real laboratory image that is no longer distributed. The `test_img.tif` in this repository is a synthetic stand-in, so they cannot be reproduced with it.

## B. The larger saved historical-data training run

Details: [app/TRAINING_GUIDE.md](app/TRAINING_GUIDE.md) (section 6, with the complete terminal workflow in section 7) and
[app/LEGACY_FINETUNING.md](app/LEGACY_FINETUNING.md).

| Item | Value |
|---|---|
| Candidate | `ft-7e4c89cb-8edc09e3` (registry status: candidate) |
| Base model | Spotiflow pretrained `general` |
| Downscale | 4 |
| Normaliser | `valid_unsaturated` |
| Train | 9,253 crops / 454 groups |
| Validation | 1,985 crops / 98 groups |
| Test | 1,980 crops / 97 groups |

Scored at a **10 native-pixel tolerance**, each model at its own recorded operating threshold:

| Measure | Pretrained `general` | Fine-tuned candidate |
|---|---:|---:|
| Precision vs saved marks | 64.89% | 75.14% |
| Recall vs saved marks | 73.95% | 91.36% |
| F1 | 69.13% | 82.46% |
| Count MAE (spots per field/page) | 3.282 | 2.014 |
| Count bias (spots per field/page) | +1.243 | +1.921 |

* F1 is **13.33 percentage points** higher for the candidate on this test split.
* The candidate has **more positive count bias**: it reports more spots per field than the marks contain.
* The two models were scored at their own thresholds (the candidate's saved threshold is 0.3). A same-threshold comparison is not in
  the saved results.
* These values are **agreement with saved researcher marks**, not general accuracy.

Limits of this result:

* The original test images are not in this repository, so inference cannot be rerun from the repository alone.
* Whether the identity mapping and the annotation completeness are right cannot be checked from the saved artifacts alone.
* The checkpoint is not in this repository. See [MODEL_CARD.md](../MODEL_CARD.md) and [artifacts/README.md](../artifacts/README.md).

## C. Application integration

* The candidate is a **registry candidate**. The saved registry has **no active model**.
* `promote` updates the ML registry. It does **not** change the detector used by the React application.
* The current app detection path does not call the registry resolver, and the React model picker lists Spotiflow's official pretrained
  names, not registry candidates.
* So **normal app detection does not use the fine-tuned model**, even after promotion. The app's default remains the official `general`
  pretrained model.
* The working path to use a candidate today is the API / CLI workflow in [app/TRAINING_GUIDE.md](app/TRAINING_GUIDE.md) (section 7.14
  and the notes on the candidate ID). Do not describe this as the app's normal detection.

## What is open

* Integration: connect detection to the registry resolver, or make the model picker list registry candidates. Tracked in
  [app/ROADMAP.md](app/ROADMAP.md).
* Same-threshold evaluation of the candidate and the pretrained model.
* An independent test set that can be shared, or an external evaluation, before any general claim.
* Scientific questions: [app/SCIENTIFIC_OPEN_QUESTIONS.md](app/SCIENTIFIC_OPEN_QUESTIONS.md).

## Reproducibility

Which results can be reproduced from this repository, and which cannot, is described in [REPRODUCIBILITY.md](REPRODUCIBILITY.md) and [MODEL_CARD.md](../MODEL_CARD.md#reproduction-limitations).
