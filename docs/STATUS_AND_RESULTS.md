# Status and results

What has been measured, on what data, and what is connected in the application. Where another document disagrees with this page, fix the other document.

All results below are agreement with saved researcher marks. None is a measure of accuracy on new laboratory images, and none shows that the software's counts are correct for a given slide. Parts A, B and C are separate; do not combine them.

| | What it is | Data | Status |
|---|---|---|---|
| **A** | Exploratory evaluation of pretrained detectors on eight slides | 8 real slides, one annotator | preliminary; not validation |
| **B** | Fine-tuning run on the saved historical data | ~13,200 crops from the historical ImageJ TIFFs; saved researcher marks | candidate model; registry status `candidate` |
| **C** | Application integration | the React app and the model registry | integrated: `promote` -> the app uses it |

## A. The eight-slide exploratory evaluation

Details: [app/ALL_SLIDES_EVAL.md](app/ALL_SLIDES_EVAL.md), [app/EVALUATION.md](app/EVALUATION.md).

* Eight real two-channel slides, one annotator.
* Marks may be incomplete. An unmarked spot is not a verified absence, so precision and recall are only partly meaningful.
* Results vary a lot between slides; sparse slides give low precision for both detectors.
* Earlier fine-tuning experiments on two or three slides showed no reliable improvement over pretrained Spotiflow at the same threshold (F1 changed by −0.03 to +0.02). See [app/FINE_TUNING.md](app/FINE_TUNING.md).
* The Spotiflow columns in the all-slides table are marked as superseded in that document; use its per-threshold tables.
* Numbers quoted for `test_img` in older documents belong to an earlier real laboratory image that is no longer distributed. The `test_img.tif` in this repository is a synthetic stand-in, so they cannot be reproduced with it.

## B. The larger saved historical-data training run

Details: [app/TRAINING_GUIDE.md](app/TRAINING_GUIDE.md) (section 6; terminal workflow in section 7), [app/LEGACY_FINETUNING.md](app/LEGACY_FINETUNING.md).

| Item | Value |
|---|---|
| Candidate | `ft-7e4c89cb-8edc09e3` (registry status: candidate) |
| Base model | Spotiflow pretrained `general` |
| Downscale / normaliser | 4 / `valid_unsaturated` |
| Train | 9,253 crops / 454 groups |
| Validation | 1,985 crops / 98 groups |
| Test | 1,980 crops / 97 groups |

Scored at a **10 native-pixel tolerance**, each model at its own recorded operating threshold (the candidate's is 0.3):

| Measure | Pretrained `general` | Fine-tuned candidate |
|---|---:|---:|
| Precision vs saved marks | 64.89% | 75.14% |
| Recall vs saved marks | 73.95% | 91.36% |
| F1 | 69.13% | 82.46% |
| Count MAE (spots per field/page) | 3.282 | 2.014 |
| Count bias (spots per field/page) | +1.243 | +1.921 |

* F1 is **13.33 percentage points** higher for the candidate on this test split. These values are **agreement with saved researcher marks**, not general accuracy.
* The candidate has **more positive count bias**: it reports more spots per field than the marks contain.
* A same-threshold comparison is not in the saved results.

Limits:

* The original test images are not in this repository, so inference cannot be rerun from it.
* Identity mapping and annotation completeness cannot be checked from the saved artifacts alone.
* The checkpoint is not in this repository. See [MODEL_CARD.md](../MODEL_CARD.md), [artifacts/README.md](../artifacts/README.md).

## C. Application integration

Integrated: `promote` -> the app uses it.

* The Spotiflow model setting defaults to `active`: the promoted model of the registry, or the pretrained `general` model when none is promoted.
* After `promote`, normal app detection uses the promoted model. A registry candidate can also be chosen by id in the model picker or the API.
* A fine-tuned model runs with the downscale and normaliser it was trained with (overriding the UI settings for that model) and its own saved threshold.
* The run record names the model by registry id and keeps the weights checksum.
* Promotion still requires the locked-test evidence ([app/TRAINING_GUIDE.md](app/TRAINING_GUIDE.md#714-promote-only-after-accepting-the-evidence)).
* In this repository the candidate `ft-7e4c89cb-8edc09e3` has status `candidate`, there is no active model, and its weights are not published. A copy of the repository on its own therefore still detects with pretrained `general`; the app uses a model only where the registry and `models/<id>` weights are in its data folder.

## What is open

* Same-threshold evaluation of the candidate and the pretrained model.
* An independent test set that can be shared, or an external evaluation, before any general claim.
* Scientific questions: [app/SCIENTIFIC_OPEN_QUESTIONS.md](app/SCIENTIFIC_OPEN_QUESTIONS.md).

## Reproducibility

What can and cannot be reproduced: [REPRODUCIBILITY.md](REPRODUCIBILITY.md), [MODEL_CARD.md](../MODEL_CARD.md#reproduction-limitations).
