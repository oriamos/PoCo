# Model card: fine-tuned Spotiflow model `ft-7e4c89cb-8edc09e3`

The model **shipped with PoCo**: the AI installer downloads it and makes it the default Spotiflow model on a fresh install (the pretrained `general` model stays available). The laboratory approved its distribution (confirmation recorded from Ori Amos; no approver name or date beyond that was recorded). It was **not** promoted through the locked-test promotion path: the registry marks it `origin: bundled` and holds no evaluation for it. The numbers below are recorded results from the original model registry (not published; the key values are in this card) and were not rerun here. Release: [model-ft-7e4c89cb-8edc09e3](https://github.com/oriamos/poco/releases/tag/model-ft-7e4c89cb-8edc09e3).

## Intended use

- Research comparison against the pretrained Spotiflow `general` model, on the same kind of two-channel microscope scans and the same counting method as the app.
- Input: single-channel crops, prepared at downscale 4 with the `valid_unsaturated` normaliser.
- Output: spot positions. The app turns these into counts after the researcher reviews them.

## Out-of-scope use

- Counting without a researcher's review.
- Any claim of general accuracy on new scanners, new samples, or other laboratories.
- Clinical or diagnostic use.
- Treating its counts as final. Its limitations (incomplete-label bias, positive-count bias, below) apply to any use.

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

- Installer: `--with-ai` downloads the model from the release above, checks size and SHA-256 against values pinned in `src/polony_app/ml/bundled_model.py`, and registers it (`origin: bundled`, log event `register_bundled`). Repeat installs reuse verified files. It becomes the active model only when none is active; an existing active model, user-trained models and a rollback are never changed.
- The app's Spotiflow model setting defaults to `active`. The model runs at downscale 4, normaliser `valid_unsaturated`, threshold 0.3 (its own saved `thresholds.yaml`); the run record names it by registry id and keeps the weights checksum. Choose pretrained `general` in the model picker, or `rollback`, to stop using it.
- User-trained candidates are unchanged: promotion still requires locked-test evidence (`--force --reason` is recorded). Registering the shipped model is a separate, logged action; it invents no evaluation.
- Opt out: `POLONY_BUNDLED_MODEL=0`. Manual retry: `python install/ai_extra.py model`. Without network the AI install still succeeds with `general`.
- **Provenance limit:** the original registry entry is not published and could not be read in this migration, so its fields (training hyperparameters, per-run evaluation log) are **not verified here**. Verified here: the SHA-256 and size of `best.pt`, that it loads and runs through PoCo's engine, and that downscale 4, `valid_unsaturated` and threshold 0.3 are applied (`install/ci/smoke_model.py`, public `config.yaml`, `thresholds.yaml`, `train_config.yaml`).

## Files and checksums

Release assets: `best.pt`, `config.yaml`, `thresholds.yaml`, `train_config.yaml`, `model.json`, `LICENSE-spotiflow.txt`, `SHA256SUMS.txt`.

| File | SHA-256 |
|---|---|
| `best.pt` (47,406,478 bytes) | `8edc09e3de3bb9da156930cd85f1d054daf6a52b937091b87fd08f0e063061fc` |
| `last.pt` (not shipped, different checkpoint) | `2dbea6ccd0c6e50970e976c7fd22fd052ae14a0bb43141fc84b1420324f68e30` |

`best.pt` is the registered weights. Verify by hand: `sha256sum -c SHA256SUMS.txt` in the download folder.

## Licence and redistribution status

| Item | Status |
|---|---|
| Spotiflow code | BSD-3-Clause. Its notice is shipped in the release (`LICENSE-spotiflow.txt`), as BSD-3 requires for redistribution. |
| Fine-tuned weights | Distribution approved by the laboratory (recorded from Ori Amos). |
| **Spotiflow pretrained weights (`general`), the base of this model** | **Open.** No separate licence or terms found: the Spotiflow README and the `spotiflow-models` repository README (a title only) state none. Whether BSD-3-Clause covers the weights is not stated. **Needed:** written confirmation from the Spotiflow authors (Dominguez Mantes, Weigert) that derivatives of the pretrained weights may be redistributed, then record it here. |
| Training data and annotations | Not distributed (unpublished laboratory data). |

The release is published on the laboratory's approval. If the authors' answer restricts redistribution, remove the release assets (`gh release delete model-ft-7e4c89cb-8edc09e3`) and set `POLONY_BUNDLED_MODEL` default off in `bundled_model.py`.

## Reproduction limitations

- The original test images are not distributed, so the evaluation cannot be rerun. The metrics come from saved artifacts. The checkpoint is in the model release, not in the git repository.
- Training procedure: [docs/app/TRAINING_GUIDE.md](docs/app/TRAINING_GUIDE.md), [docs/app/FINE_TUNING.md](docs/app/FINE_TUNING.md).
