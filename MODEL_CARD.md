# Model card: fine-tuned Spotiflow candidate `ft-7e4c89cb-8edc09e3`

This card describes one candidate model. It is a **registry candidate**, not an approved model. The model registry has no
active model. The numbers below are recorded results from the saved model registry (not published here; the key values are in this card). They were not
rerun for this card.

## Intended use

- A candidate for research comparison against the pretrained Spotiflow `general` model, on the same kind of two-channel
  microscope scans and the same counting method as the app.
- Input: single-channel crops, prepared at downscale 4 with the `valid_unsaturated` normaliser.
- Output: spot positions. The app turns these into counts after the researcher reviews them.

## Out-of-scope use

- Counting without a researcher's review.
- Any claim of general accuracy on new scanners, new samples, or other laboratories.
- Clinical or diagnostic use.
- Use as the default model in the app. The app does not use this candidate (see Integration status).

## Base model

Spotiflow pretrained model `general`. The candidate was fine-tuned from it.

## Training data route

Historical ImageJ-annotated TIFFs. The researcher's embedded marks were used as positive labels, and only field and page
pairs with marks or with explicit examination evidence were included. The original TIFFs are not in this repository.

## Split policy

- Splits are made by group (specimen, slide, or identical file bytes), so related material does not cross splits.
- The test set is locked. A lock file records the test groups and the hash of the test crops.
- Crop counts and group counts:

| Split | Crops | Groups |
|---|---:|---:|
| Train | 9,253 | 454 |
| Validation | 1,985 | 98 |
| Test | 1,980 | 97 |

## Metrics

Evaluated on the locked test set at a 10 native-pixel tolerance. These numbers measure **agreement with the saved
researcher marks**. They are not general accuracy.

| Measure | Pretrained `general` | Candidate |
|---|---:|---:|
| Precision | 64.89% | 75.14% |
| Recall | 73.95% | 91.36% |
| F1 | 69.13% | 82.46% |
| Count MAE (spots per field or page) | 3.282 | 2.014 |
| Count bias (spots per field or page) | +1.243 | +1.921 |

The candidate's F1 is 13.33 percentage points higher than the pretrained model's F1 on this test set. That gain does not
show that the candidate is 82.46% accurate on new laboratory images.

## Thresholds

Each model was evaluated with its own recorded operating threshold (`prob_thresh=None`). The candidate's recorded
threshold is 0.3 ([thresholds.yaml](artifacts/ft-7e4c89cb-8edc09e3/thresholds.yaml)). This is not a controlled
comparison at one shared threshold. A same-threshold evaluation is not documented in the repository.

## Limitations

- The labels are one researcher's marks. A real polony that the researcher did not mark counts as a false positive in
  precision and is treated as background during training. The model can learn to suppress such spots.
- The test set comes from the laboratory's historical files. The result may not hold for other scanners, stains, or
  samples.
- Identity mapping (which specimen and slide each file belongs to) and annotation completeness cannot be verified from the
  saved artifacts alone. The importer's identity checks were recorded, but they were not checked against laboratory
  records here.

## Incomplete-label bias

Because the reference marks are incomplete, precision and recall measure agreement with those marks. They do not measure
agreement with every real spot. A model that finds real spots the researcher missed will look worse on these metrics.

## Positive-count bias

The candidate's count bias is more positive than the pretrained model's (+1.921 against +1.243 spots per field or page),
so on average it counts more spots above the reference marks than the pretrained model does. Its lower count MAE does not
remove this bias. Check the count bias before using the candidate for counts.

## Integration status

- The candidate is in the model registry with status `candidate`. The registry has no active model.
- Promotion updates the registry. The React and app detection path does **not** call the registry resolver. Promotion
  therefore does not replace the default `general` model in the app.
- The app's default detection model is still Spotiflow `general`.

## Checkpoint checksum

The checkpoint files are **not** in this repository. Their SHA-256 hashes, recorded in
the saved model registry (not published with this repository), are:

| File | SHA-256 |
|---|---|
| `best.pt` | `8edc09e3de3bb9da156930cd85f1d054daf6a52b937091b87fd08f0e063061fc` |
| `last.pt` | `2dbea6ccd0c6e50970e976c7fd22fd052ae14a0bb43141fc84b1420324f68e30` |

The registry records `best.pt` as the registered weights. `last.pt` is the final epoch and is not registered.

## Licence and redistribution status

TODO (Ori): state the licence of the checkpoints and of the base Spotiflow weights, and whether they may be redistributed.
This is unverified. Until it is settled, the checkpoints are not published here.

The training data is research data and is not in this repository. Redistribution of the data is unverified.

## Reproduction limitations

- The original test images are not in the repository. Inference cannot be rerun from the repository alone.
- The checkpoint files are not in the repository.
- The metrics above come from saved artifacts. Rerunning them needs the checkpoint files and the original scans, and
  neither is in the repository.
- See [docs/app/TRAINING_GUIDE.md](docs/app/TRAINING_GUIDE.md) and [docs/app/FINE_TUNING.md](docs/app/FINE_TUNING.md) for the
  training procedure.
