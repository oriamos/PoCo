# Shipped model metadata and locked test set

Status of all experiments: [docs/STATUS_AND_RESULTS.md](../docs/STATUS_AND_RESULTS.md).

## In this repository

| Path | What |
|---|---|
| `ft-7e4c89cb-8edc09e3/config.yaml`, `train_config.yaml`, `thresholds.yaml` | configuration and thresholds of the fine-tuned candidate |
| `test-set/test_lock.json` | the locked test set (specimen groups, image hashes, lock checksum) used for every evaluation |

## Not in this repository

* **Weights** are not in git; `best.pt` is a [release asset](https://github.com/oriamos/poco/releases/tag/model-ft-7e4c89cb-8edc09e3) the AI installer downloads and verifies. `last.pt` is not distributed. Checksums and licence status: [MODEL_CARD.md](../MODEL_CARD.md).
* **Dataset snapshot manifest** (`snapshot_manifest.json`): lists the laboratory's slide file names and sample codes, which are unpublished research identifiers. The lock file remains.
* **Model registry** (`registry.json`): its evaluation log names laboratory slides by sample code and date. Its checkpoint checksums are copied into [MODEL_CARD.md](../MODEL_CARD.md).
* **Original images**: the laboratory TIFFs.

## How this record is used

These files are a provenance record of the saved candidate. The training and evaluation CLI loads registry artifacts from `<data_dir>/models`. The app uses a model from that registry only when the registry and `models/<id>` weights are in its data folder. The AI installer puts the shipped model there and registers it as the default; your own trained models need `promote` ([TRAINING_GUIDE.md](../docs/app/TRAINING_GUIDE.md#714-promote-only-after-accepting-the-evidence)). Copying a model folder alone does not register or activate it.

Results, configuration and limitations: [TRAINING_GUIDE.md](../docs/app/TRAINING_GUIDE.md). The test crops and original images needed to rerun the evaluation are not included, so it cannot be rerun from this repository alone.
