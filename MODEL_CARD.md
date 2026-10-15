# Model card: fine-tuned Spotiflow candidate `ft-7e4c89cb-8edc09e3`

A **registry candidate**, not an approved model; the model registry has no active model. The numbers are recorded results from the saved model registry (not published here; the key values are in this card). They were not rerun for this card.

## Intended use

- Research comparison against the pretrained Spotiflow `general` model, on the same kind of two-channel microscope scans and the same counting method as the app.
- Input: single-channel crops, prepared at downscale 4 with the `valid_unsaturated` normaliser.
- Output: spot positions. The app turns these into counts after the researcher reviews them.

## Out-of-scope use

- Counting without a researcher's review.
- Any claim of general accuracy on new scanners, new samples, or other laboratories.
- Clinical or diagnostic use.
- Use as the app's default model without promotion with locked-test evidence. Its limitations (incomplete-label bias, positive-count bias, below) apply to any use.

## Base model

Spotiflow pretrained `general`; the candidate was fine-tuned from it.

## Training data route

Historical ImageJ-annotated TIFFs; the researcher's embedded marks are the positive labels. In the default `marked-only` mode used for this run, only field and page pairs with at least one embedded mark were included. A pair without marks was left out, not treated as zero; the run has no verified-zero fields. The original TIFFs are not in this repository.

## Split policy

- Splits are by group (specimen, slide, or identical file bytes), so related material does not cross splits.
- The test set is locked: a lock file records the test groups and the hash of the test crops.

| Split | Crops | Groups |
|---|---:|---:|
| Train | 9,253 | 454 |
| Validation | 1,985 | 98 |
| Test | 1,980 | 97 |

## Metrics

Locked test set, 10 native-pixel tolerance. These numbers measure **agreement with the saved researcher marks**, not general accuracy.

| Measure | Pretrained `general` | Candidate |
|---|---:|---:|
| Precision | 64.89% | 75.14% |
| Recall | 73.95% | 91.36% |
| F1 | 69.13% | 82.46% |
| Count MAE (spots per field or page) | 3.282 | 2.014 |
| Count bias (spots per field or page) | +1.243 | +1.921 |

The F1 gain is 13.33 percentage points. It does not show that the candidate is 82.46% accurate on new laboratory images.

## Thresholds

Each model used its own recorded operating threshold (`prob_thresh=None`). The candidate's is 0.3 ([thresholds.yaml](artifacts/ft-7e4c89cb-8edc09e3/thresholds.yaml)). This is not a comparison at one shared threshold, and no same-threshold evaluation is documented in the repository.

## Limitations

- The labels are one researcher's marks.
- The test set comes from the laboratory's historical files; the result may not hold for other scanners, stains, or samples.
- Identity mapping (which specimen and slide each file belongs to) and annotation completeness cannot be verified from the saved artifacts alone. The importer's identity checks were recorded but not checked against laboratory records here.

## Incomplete-label bias

A real polony the researcher did not mark counts as a false positive in precision and is background during training, so the model can learn to suppress such spots. Precision and recall measure agreement with the marks, not with every real spot; a model that finds spots the researcher missed looks worse.

## Positive-count bias

The candidate's count bias is more positive than the pretrained model's (+1.921 against +1.243 spots per field or page): on average it counts more spots above the reference marks. Its lower count MAE does not remove this bias. Check the count bias before using the candidate for counts.

## Integration status

- Registry status: `candidate`; no active model.
- The app's Spotiflow model setting defaults to `active` (the promoted model, else pretrained `general`). After `promote`, app detection uses the promoted model. A registry candidate can also be chosen by id in the model picker or API.
- A fine-tuned model runs with the downscale and normaliser it was trained with and its own saved threshold. The run record names it by registry id and keeps the weights checksum.
- Promotion requires the locked-test evidence.
- The weights are not published, so a copy of this repository on its own detects with pretrained `general`. The app uses the model only where the registry and `models/<id>` weights are in its data folder.

## Checkpoint checksum

The checkpoint files are **not** in this repository. SHA-256 hashes recorded in the saved model registry (not published):

| File | SHA-256 |
|---|---|
| `best.pt` | `8edc09e3de3bb9da156930cd85f1d054daf6a52b937091b87fd08f0e063061fc` |
| `last.pt` | `2dbea6ccd0c6e50970e976c7fd22fd052ae14a0bb43141fc84b1420324f68e30` |

The registry records `best.pt` as the registered weights; `last.pt` is the final epoch and is not registered.

## Licence and redistribution status

**Decision: the checkpoints are not published in this repository.** Findings, as far as they could be checked:

| Item | Finding |
|---|---|
| Spotiflow code | BSD-3-Clause (stated on the [Spotiflow repository](https://github.com/weigertlab/spotiflow)). |
| Spotiflow pretrained weights (`general`) | The Spotiflow README states no separate licence or terms for the pretrained weights, which the package downloads on first use. Whether BSD-3-Clause covers them is not stated. Not verified. |
| Fine-tuned checkpoints (`best.pt`, `last.pt`) | Derived from the pretrained weights and trained on the laboratory's historical annotated slides. Redistribution rights follow the weights' terms and the laboratory's rights over the data and annotations. Not verified. |
| Training data and annotations | Unpublished laboratory research data, not in this repository. Redistribution not verified. |

To publish the weights, settle and record here: (1) the licence of the pretrained Spotiflow weights, from the Spotiflow authors or their publication; (2) the laboratory's permission to release a model trained on its data; (3) the SHA-256 values above, published next to the files (for example as assets of a versioned release). Until then the checksums identify files held by the laboratory, and nobody can obtain them from this repository.

## Reproduction limitations

- The original test images and the checkpoint files are not in the repository, so inference cannot be rerun from it. The metrics come from saved artifacts.
- Training procedure: [docs/app/TRAINING_GUIDE.md](docs/app/TRAINING_GUIDE.md), [docs/app/FINE_TUNING.md](docs/app/FINE_TUNING.md).
