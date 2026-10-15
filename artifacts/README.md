# Shipped model metadata and locked test set

Status of all experiments: [docs/STATUS_AND_RESULTS.md](../docs/STATUS_AND_RESULTS.md).

## In this repository

| Path | What |
|---|---|
| `ft-7e4c89cb-8edc09e3/config.yaml`, `train_config.yaml`, `thresholds.yaml` | configuration and thresholds of the fine-tuned candidate |
| `test-set/test_lock.json` | the locked test set (specimen groups, image hashes, lock checksum) used for every evaluation |

## Not in this repository

* **Weights** (`best.pt`, `last.pt`): redistribution rights depend on the Spotiflow base model and the research data, and have not been verified. Status and identifying checksums: [MODEL_CARD.md](../MODEL_CARD.md).
* **Dataset snapshot manifest** (`snapshot_manifest.json`): lists the laboratory's slide file names and sample codes, which are unpublished research identifiers. The lock file remains.
* **Model registry** (`registry.json`): its evaluation log names laboratory slides by sample code and date. Its checkpoint checksums are copied into [MODEL_CARD.md](../MODEL_CARD.md).
* **Original images**: the laboratory TIFFs.

If the weights or the manifest are later released (for example as a versioned release asset with checksums), this page will say where.

## How this record is used

These files are a provenance record of the saved candidate. The training and evaluation CLI loads registry artifacts from `<data_dir>/models`. The app uses a model from that registry only when the registry and `models/<id>` weights are in its data folder, and only after `promote` or when chosen by id ([TRAINING_GUIDE.md](../docs/app/TRAINING_GUIDE.md#714-promote-only-after-accepting-the-evidence)). Copying the candidate folder alone does not register or activate it. The saved registry records the candidate with no active model.

Results, configuration and limitations: [TRAINING_GUIDE.md](../docs/app/TRAINING_GUIDE.md). The test crops and original images needed to rerun the evaluation are not included, so it cannot be rerun from this repository alone.
