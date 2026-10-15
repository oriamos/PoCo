# Shipped model metadata and locked test set

> One authoritative status page for all experiments: [docs/STATUS_AND_RESULTS.md](../docs/STATUS_AND_RESULTS.md).

## What is in this repository

| Path | What |
|---|---|
| `ft-7e4c89cb-8edc09e3/config.yaml`, `train_config.yaml`, `thresholds.yaml` | configuration and thresholds of the fine-tuned candidate |
| `test-set/test_lock.json` | the locked test set (specimen groups, image hashes, lock checksum) used for every evaluation |

## What is not in this repository

* **Weights** (`best.pt`, `last.pt`) are not included. Their redistribution rights depend on the Spotiflow base model and on the
  research data they were trained on, and these have not been verified. See [MODEL_CARD.md](../MODEL_CARD.md) for the status and
  the checksums that identify the files.
* **Dataset snapshot manifest** (`snapshot_manifest.json`) is not included. It lists the laboratory's own slide file names and sample
  codes, which are unpublished research identifiers. The lock file remains.
* **Model registry** (`registry.json`) is not included. Its evaluation log names the laboratory slides by sample code and date. The checkpoint checksums it contains are copied into [MODEL_CARD.md](../MODEL_CARD.md).
* **Original images** are not included. The laboratory TIFFs are not in the repository.

If the weights or the manifest are later released (for example as a versioned release asset with checksums), this page will say where
to find them.

## How this record is used

These files are a provenance record of the saved candidate. The training and evaluation CLI loads registry artifacts from
`<data_dir>/models`. Current app detection is not automatically wired to that registry (see
[TRAINING_GUIDE.md](../docs/app/TRAINING_GUIDE.md#714-promote-only-after-accepting-the-evidence)). Copying the candidate folder alone
does not register or activate it. The saved registry records the candidate with no active model.

The recorded results, configuration and limitations are in [TRAINING_GUIDE.md](../docs/app/TRAINING_GUIDE.md). The test crops and
original images needed to rerun the evaluation are not included, so the evaluation cannot be rerun from this repository alone.
