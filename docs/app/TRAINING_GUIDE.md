# Model training — start here
> Status and what is connected to the application: [STATUS_AND_RESULTS.md](../STATUS_AND_RESULTS.md) (this page does not change that status).

Training is run from a terminal with `python -m polony_app.ml`. There is no training button in the React interface and nothing trains automatically. The overnight **experiment Run** button runs detection, not training.

## Quick path
Historical TIFF folder to promoted model. One block at a time; stop at any blocker. Details: directories [7.1](#71-choose-permanent-directories) and [7.2](#72-create-the-python-environment-and-install-spotiflow), TIFFs [7.3](#73-put-the-tiffs-in-the-input-directory), mapping [7.4](#74-generate-and-complete-the-mapping-templates), preflight/import [7.5](#75-run-the-independent-preflight)–[7.7](#77-build-the-immutable-snapshot), lock [7.8](#78-lock-the-test-set--irreversible-without-an-explicit-replacement), train [7.12](#712-train-the-candidate), evaluate [7.13](#713-evaluate-candidate-and-baseline-on-the-same-locked-test-set), promote [7.14](#714-promote-only-after-accepting-the-evidence).

```bash
# 1 directories, ml command (environment from 7.2 installed)
cd /path/to/polony-counting
export POLONY_RUN_ROOT=/data/polony-training POLONY_TIFF_DIR=/data/polony-training/tiffs POLONY_WORK_DIR=/data/polony-training/work
export POLONY_DATA_DIR=/data/polony-training/appdata POLONY_DEVICE=auto POLONY_WORKERS=4 POLONY_PY=/data/polony-training/venv/bin/python
ml() { PYTHONPATH=src "$POLONY_PY" -m polony_app.ml --data-dir "$POLONY_DATA_DIR" "$@"; }
# 2 copy TIFFs, write mapping templates, then EDIT channels.json and identities.json
rsync -ah --info=progress2 /path/to/source-tiffs/ "$POLONY_TIFF_DIR/"
ml import-legacy --input "$POLONY_TIFF_DIR" --write-templates "$POLONY_WORK_DIR/templates"
cp "$POLONY_WORK_DIR/templates/channels.template.json" "$POLONY_WORK_DIR/channels.json"; cp "$POLONY_WORK_DIR/templates/identities.template.json" "$POLONY_WORK_DIR/identities.json"
# 3 preflight, dry-run (require BLOCKERS: none), import
ml preflight --input "$POLONY_TIFF_DIR" --channel-map "$POLONY_WORK_DIR/channels.json" --identity-map "$POLONY_WORK_DIR/identities.json" --downscale 4 --normaliser valid_unsaturated --fractions 0.7,0.15,0.15
ml import-legacy --input "$POLONY_TIFF_DIR" --channel-map "$POLONY_WORK_DIR/channels.json" --identity-map "$POLONY_WORK_DIR/identities.json" --downscale 4 --normaliser valid_unsaturated --fractions 0.7,0.15,0.15 --batch-size 4 --epochs 10 --dry-run
ml import-legacy --input "$POLONY_TIFF_DIR" --channel-map "$POLONY_WORK_DIR/channels.json" --identity-map "$POLONY_WORK_DIR/identities.json" --downscale 4 --normaliser valid_unsaturated --fractions 0.7,0.15,0.15 --workers "$POLONY_WORKERS"
# 4 snapshot ID printed by the import: verify, split, lock the test set once
export POLONY_SNAPSHOT=ds-REPLACE_WITH_THE_PRINTED_VERSION
ml verify "$POLONY_SNAPSHOT"; ml split --snapshot "$POLONY_SNAPSHOT"; ml split --snapshot "$POLONY_SNAPSHOT" --lock-test
# 5 train
ml train --snapshot "$POLONY_SNAPSHOT" --base general --device "$POLONY_DEVICE" --batch-size 4 --lr 1e-4 --epochs 10 --early-stopping-patience 3 --num-workers "$POLONY_WORKERS" --notes "historical ImageJ marks; downscale 4; reviewed mappings"
# 6 evaluate candidate and baseline, compare
export POLONY_CANDIDATE=ft-REPLACE_WITH_THE_FINAL_CANDIDATE_ID
ml eval-model --model "$POLONY_CANDIDATE" --device "$POLONY_DEVICE"; ml eval-model --model general --downscale 4 --normaliser valid_unsaturated --device "$POLONY_DEVICE"
ml compare --models "$POLONY_CANDIDATE" general
# 7 promote only if the comparison supports it
ml promote "$POLONY_CANDIDATE" --app-downscale 4 --app-normaliser valid_unsaturated --reason "better locked-test F1 and count MAE; reviewed count bias and failure cases"
```

Check in the app: with the app data folder set to `$POLONY_DATA_DIR`, run detection; the model setting `active` now uses the promoted model ([7.14](#714-promote-only-after-accepting-the-evidence)).

## 1. What is being trained?
PoCo **fine-tunes Spotiflow**: it starts from the pretrained detector `general` and adjusts its weights using the researcher's marked polonies. Big-FISH is a separate classical detector and is not trained.
The network takes a single-channel image and learns spot positions. It is not a three-colour classifier: channel mapping and the app's red/green matching give the red/green/yellow counts. A folder named `yellow` does not mean a yellow class was learned.

## 2. Which parts of an image become examples?
A **field** is a grid square. A **crop** is the image cut from one field on one TIFF page. One TIFF can give several crops; crop count is not slide count.

| Your labels | Command | What can enter the dataset |
|---|---|---|
| Historical ImageJ marks embedded in TIFFs | `import-legacy` | Only field/page pairs with marks on that page, or explicitly verified zero counts in an examined-fields manifest |
| Corrections made in the app | `build` | Fully reviewed rectangular regions with a confirmed channel mapping; exclusions and unresolved points can make a crop ineligible |

- For historical files, **no marks does not mean zero**. A grid square without evidence of examination is left out; marks on page 0 do not prove the same square on page 1 was examined.
- Default `marked-only` mode has no verified-zero examples. For genuinely empty counted fields use the manifest route in [LEGACY_FINETUNING.md](LEGACY_FINETUNING.md). Inside an included crop, the supplied marks are the positive labels. If the researcher missed a real spot, training can teach the model to suppress it: "examined" is an eligibility rule, not proof of perfect annotation.

## 3. Why are there three data sets?
| Split | Purpose | Updates weights? |
|---|---|---|
| **Train** | Examples the network learns from | Yes |
| **Validation** (`val`) | Select the best saved epoch, control early stopping, optimise the detection threshold | No, but it influences model selection |
| **Test** | Compare the selected candidate with the baseline after training | No |

- Default target fractions are 70% / 15% / 15%, applied to independent groups (crops of one group stay together), so crop percentages need not match. Specimen/slide identities and byte-identical files prevent related material crossing splits; correct identity mapping matters.
- A **snapshot** freezes the exported crops, labels, settings and split assignments. A **test lock** freezes the test material across later snapshots.
- Repeatedly choosing settings because they improve the same test results makes that test part of model development; reserve new independent data for a final claim.

## 4. What do the settings mean?
| Setting | Meaning |
|---|---|
| `--base general`, `--epochs 10`, `--batch-size 4`, `--lr 1e-4` | Start from pretrained weights; up to 10 epochs (early stopping may end sooner); four examples per optimiser step; learning rate (size of weight updates) |
| `--downscale 4` on the snapshot | Reduce each spatial dimension by four before training/evaluation; original crops stay at native resolution |
| `--crop-size 256` on training | Spotiflow's training patch size in the prepared image; separate from grid-field size and downscale |
| `--normaliser valid_unsaturated` | Use recorded page-level intensity statistics; do not stretch each crop independently |
| `--early-stopping-patience 3` | Stop after this many epochs without validation-loss improvement; the best checkpoint is kept |
| `--device auto` | GPU if available, otherwise CPU; check the printed resolved device |
| `--dry-run` | Print the plan and size without fitting; an import dry-run can still print blockers while exiting 0 |

Train and run a candidate with the same downscale and normaliser. Downscale 4 is the setting of the saved run below, not a guarantee of optimality for every scanner.

## 5. How to read the training screen
**Loss is an optimisation score, not an accuracy percentage.** A validation loss of `0.432` is not 43.2% error, and a 4.4% loss reduction is not 4.4 percentage points more detection accuracy.

The saved run's validation loss fell from `0.451747` at the first logged epoch to a best of `0.431678` (about 4.44% lower) at index **7**, the **eighth** epoch. The final tenth epoch reached `0.441449`; `best.pt`, not the final weights, is registered. Lower loss alone does not show that fine-tuning beats `general`.

Evaluate candidate and baseline on the same locked test crops:

- **Precision:** fraction of predicted spots that match a researcher mark. **Recall:** fraction of marks found.
- **F1:** balances precision and recall; not "accuracy". **Count MAE:** average absolute difference in spots per evaluated field/page. **Count bias:** average predicted minus reference; positive means over-counting.

Matching is one-to-one within a stated distance. Read 5, 10 and 15 native-pixel tolerances together. A missing human mark can count as a false positive, and equal totals do not prove the correct spots were found.

## 6. Results actually saved in this repository
Source: `artifacts/registry.json` (not published; see [artifacts/README.md](../../artifacts/README.md)), `snapshot_manifest.json` (not published), [`test_lock.json`](../../artifacts/test-set/test_lock.json) and the [checkpoint files](../../artifacts/ft-7e4c89cb-8edc09e3). Recorded results from 15 October 2026, not a fresh rerun on the original images.

Candidate `ft-7e4c89cb-8edc09e3`; base `general`; downscale 4; normaliser `valid_unsaturated`. 10 epochs on **CPU** (despite requesting `auto`) in about 32.6 minutes. It remains a **candidate**; the saved registry has no active model.

| Split | Crops | Groups | Labelled points before preparation |
|---|---:|---:|---:|
| Train | 9,253 | 454 | 89,456 |
| Validation | 1,985 | 98 | 19,421 |
| Test | 1,980 | 97 | 17,623 |

- All **13,218** crops carry `researcher_examined: true`; all are page 0 mapped as `red`. **14,611** unknown field/page pairs were excluded; **zero** verified-zero fields.
- The manifest has 1,252 source records and 1,041 distinct source-image hashes; neither is the number of independent specimens. The import reports 1,041 confirmed contributing identities and zero unconfirmed, although `allow_unconfirmed_identity` was enabled; the mapping cannot be confirmed against laboratory records from these artifacts alone.

At **10 native-pixel tolerance**, same lock and configuration:

| Measure | Pretrained `general` | Fine-tuned candidate |
|---|---:|---:|
| Precision vs marks | 64.89% | 75.14% |
| Recall vs marks | 73.95% | 91.36% |
| F1 | 69.13% | 82.46% |
| Count MAE, spots per field/page | 3.282 | 2.014 |
| Count bias, spots per field/page | +1.243 | +1.921 |

- Higher recorded F1 and lower count MAE, but **more positive count bias**. The F1 gain is **13.33 percentage points**; agreement with marks is not accuracy, and 82.46% is not proof of accuracy on new laboratory images.
- Both evaluations pass `prob_thresh=None`, so each model uses its own threshold (candidate's saved best: 0.3): recorded operating points, not a same-threshold experiment.
- Test groups were checked only against saved records, not original samples; no raw test crops are in the repository, so inference cannot be rerun.
- The older eight-slide / leave-specimen-out experiments in other documents concern different runs; do not present their findings as this run's result, or as disproven by it.

## 7. Complete terminal workflow — historical ImageJ TIFFs
The path used for the large historical dataset. One block at a time; stop at any blocker. Bash on macOS/Linux; on Windows run the same Python commands in PowerShell (path and variable syntax differs).

### 7.1 Choose permanent directories
About 60 GB free for input, snapshots, staging and models (the dry-run prints an estimate). Replace the example paths once:

```bash
cd /path/to/polony-counting
export POLONY_RUN_ROOT=/data/polony-training POLONY_TIFF_DIR=/data/polony-training/tiffs POLONY_WORK_DIR=/data/polony-training/work
export POLONY_DATA_DIR=/data/polony-training/appdata POLONY_DEVICE=auto POLONY_WORKERS=4
mkdir -p "$POLONY_RUN_ROOT" "$POLONY_TIFF_DIR" "$POLONY_WORK_DIR" "$POLONY_DATA_DIR"
```

Snapshots, test lock and registry must share one `POLONY_DATA_DIR`; do not change the TIFF directory after starting the import.

### 7.2 Create the Python environment and install Spotiflow
Python 3.10–3.13. The helper installs a matching PyTorch/torchvision pair and Spotiflow; `--cuda auto` uses NVIDIA CUDA if detected, Apple MPS on Apple Silicon, otherwise CPU.

```bash
python3 -m venv "$POLONY_RUN_ROOT/venv"
export POLONY_PY="$POLONY_RUN_ROOT/venv/bin/python"
"$POLONY_PY" -m pip install --upgrade pip
"$POLONY_PY" -m pip install -r requirements-app.txt
"$POLONY_PY" install/ai_extra.py install --cuda auto
"$POLONY_PY" install/ai_extra.py check
ml() { PYTHONPATH=src "$POLONY_PY" -m polony_app.ml --data-dir "$POLONY_DATA_DIR" "$@"; }
ml --help
```

Expected: the help lists `import-legacy`, `preflight`, `verify`, `split`, `gpu-smoke`, `train`, `eval-model`, `compare`, `promote` and `rollback`.

AMD ROCm: use the ROCm installation in [`scripts/runbook/real_training.sh`](../../scripts/runbook/real_training.sh) instead of `ai_extra.py`, and set `POLONY_DEVICE=rocm` (alias for PyTorch's `cuda` API). An explicitly requested unavailable GPU is refused, not replaced by CPU; `auto` may fall back to CPU and prints the resolved device.

### 7.3 Put the TIFFs in the input directory
Keep the original tree and file names; do not add research images to Git. The importer searches recursively and does not open archives.

```bash
rsync -ah --info=progress2 /path/to/source-tiffs/ "$POLONY_TIFF_DIR/"
find "$POLONY_TIFF_DIR" -type f \( -iname '*.tif' -o -iname '*.tiff' \) | wc -l
```

### 7.4 Generate and complete the mapping templates
```bash
ml import-legacy --input "$POLONY_TIFF_DIR" --write-templates "$POLONY_WORK_DIR/templates"
cp "$POLONY_WORK_DIR/templates/channels.template.json" "$POLONY_WORK_DIR/channels.json"
cp "$POLONY_WORK_DIR/templates/identities.template.json" "$POLONY_WORK_DIR/identities.json"
```

Edit both copies before continuing (schemas: [LEGACY_FINETUNING.md](LEGACY_FINETUNING.md#3-files-you-provide)):

- `channels.json`: fill `confirmed_by`, `confirmed_on`, `source_of_truth`; confirm which TIFF page is red/green and whether it is trained. Do not infer colour from a folder or file name.
- `identities.json`: verify every `specimen_id`, `slide_id`, assay and replicate against laboratory records; set `confirmed: true` only after checking.
- With explicit records of fields counted as zero, also copy and complete `examined-fields.template.json` and use the verified-zero variant (7.5–7.7). Do not turn blank/unmarked fields into zeroes.

### 7.5 Run the independent preflight
```bash
ml preflight --input "$POLONY_TIFF_DIR" --channel-map "$POLONY_WORK_DIR/channels.json" \
  --identity-map "$POLONY_WORK_DIR/identities.json" --downscale 4 \
  --normaliser valid_unsaturated --fractions 0.7,0.15,0.15
```

Expected: exit code 0 (`echo $?`). Fix every mapping, identity or file-layout problem first. Verified-zero variant: add `--mode examined-fields-manifest --examined-fields "$POLONY_WORK_DIR/examined-fields.json"`.

### 7.6 Dry-run the import
Default `marked-only` mode: only field/page pairs with at least one embedded mark are eligible.

```bash
ml import-legacy --input "$POLONY_TIFF_DIR" --channel-map "$POLONY_WORK_DIR/channels.json" \
  --identity-map "$POLONY_WORK_DIR/identities.json" --downscale 4 --normaliser valid_unsaturated \
  --fractions 0.7,0.15,0.15 --batch-size 4 --epochs 10 --dry-run
```

**Verified-zero variant** (only if the manifest holds genuine evidence for zero-counted fields): add the same two options as in 7.5; use the same mode and files for the real import.

Confirm in the report: `BLOCKERS: none`; expected TIFF count and rejected-file reasons; page-to-channel mapping; included field/page pairs and those excluded as unproven; confirmed identities and train/validation/test group counts; estimated disk and memory. The dry-run exits 0 even when it prints `BLOCKERS`; continue only when there are none.

### 7.7 Build the immutable snapshot
The 7.6 command without `--dry-run`, `--batch-size` and `--epochs`, plus workers (same mode and files):

```bash
ml import-legacy --input "$POLONY_TIFF_DIR" --channel-map "$POLONY_WORK_DIR/channels.json" \
  --identity-map "$POLONY_WORK_DIR/identities.json" --downscale 4 --normaliser valid_unsaturated \
  --fractions 0.7,0.15,0.15 --workers "$POLONY_WORKERS"
```

The output ends with a version such as `ds-7e4c89cb...`. Copy it exactly:

```bash
export POLONY_SNAPSHOT=ds-REPLACE_WITH_THE_PRINTED_VERSION
ml verify "$POLONY_SNAPSHOT"
ml split --snapshot "$POLONY_SNAPSHOT"
```

Expected: `verify` prints `intact`; `split` shows the group-to-split table. Stop if train or validation is empty, identities look wrong, or related slides sit in different splits.

### 7.8 Lock the test set — irreversible without an explicit replacement
After inspecting the split (do this once):

```bash
ml split --snapshot "$POLONY_SNAPSHOT" --lock-test
```

Expected: `LOCKED test set`. Later snapshots keep locked specimens, slides and byte-identical files out of train/validation. Replacing a lock needs `--replace-lock --reason "..."`, changes the scientific test set, and must be exceptional and documented.

### 7.9 Check the selected compute device
```bash
ml gpu-smoke --device "$POLONY_DEVICE"
```

Expected: device information, then successful forward/backward checks. CPU is valid but slower (saved run: about 32.6 minutes, 20-core CPU).

### 7.10 Validate the training plan without training
```bash
ml train --snapshot "$POLONY_SNAPSHOT" --base general --device "$POLONY_DEVICE" --batch-size 4 \
  --epochs 10 --early-stopping-patience 3 --num-workers "$POLONY_WORKERS" --dry-run
```

Expected: integrity, no test leakage, crop counts, device, memory mode, steps per epoch, validation cost, ending with `Training will not start because --dry-run was supplied.` No model is created.

### 7.11 Optional one-epoch timing run
A real run that registers a separate candidate (not resumed into the final run); use only to estimate runtime:

```bash
ml train --snapshot "$POLONY_SNAPSHOT" --base general --device "$POLONY_DEVICE" --batch-size 4 \
  --epochs 1 --num-workers "$POLONY_WORKERS" --notes "one-epoch timing benchmark"
```

### 7.12 Train the candidate
```bash
ml train --snapshot "$POLONY_SNAPSHOT" --base general --device "$POLONY_DEVICE" --batch-size 4 \
  --lr 1e-4 --epochs 10 --early-stopping-patience 3 --num-workers "$POLONY_WORKERS" \
  --notes "historical ImageJ marks; downscale 4; reviewed mappings"
```

Expected: a final line `registered candidate ft-...`. The best-validation-loss checkpoint is saved; the last epoch is reported separately. Copy the final candidate ID, not the benchmark's:

```bash
export POLONY_CANDIDATE=ft-REPLACE_WITH_THE_FINAL_CANDIDATE_ID
ml list models
```

Expected: status `candidate`, dataset `$POLONY_SNAPSHOT`, configuration downscale 4 / `valid_unsaturated`; not active yet.

### 7.13 Evaluate candidate and baseline on the same locked test set
```bash
ml eval-model --model "$POLONY_CANDIDATE" --device "$POLONY_DEVICE"
ml eval-model --model general --downscale 4 --normaliser valid_unsaturated --device "$POLONY_DEVICE"
ml compare --models "$POLONY_CANDIDATE" general
```

The candidate uses the configuration stored at training; the explicit baseline settings give `general` the same downscale and normalisation. Compare precision, recall, F1, count MAE and count bias at 5, 10 and 15 native pixels; do not decide from validation loss alone. For a stricter same-threshold comparison, rerun both `eval-model` commands with the same explicit `--prob-thresh VALUE` and keep that result separate from the own-optimised-threshold comparison.

### 7.14 Promote only after accepting the evidence
Promote if the comparison supports the candidate and the app will run it at downscale 4 with `valid_unsaturated`:

```bash
ml promote "$POLONY_CANDIDATE" --app-downscale 4 --app-normaliser valid_unsaturated \
  --reason "better locked-test F1 and count MAE; reviewed count bias and failure cases"
ml list models
```

Do not use `--force` merely to bypass a failed comparison. Promotion changes only the registry in `$POLONY_DATA_DIR`; it does not rewrite previous analyses. In the app:

- The Spotiflow model setting defaults to `active`: the promoted registry model, or pretrained `general` when none is promoted.
- After `promote` no restart is needed. Run detection as usual (the app's data folder must be the same `POLONY_DATA_DIR`, containing the registry and `models/<id>`); the Detect tab model picker shows "promoted model (id)".
- A registry candidate can also be chosen by id in the picker or the API (`spotiflow.model_name`). A fine-tuned model runs with the downscale and normaliser it was trained with (the UI's values are overridden for it) and its own saved threshold.
- Engine-runs table and provenance name the model by registry id and keep the weights checksum.

Undo with `ml rollback` (returns to the previous promoted model, or to pretrained `general`); check with `ml list models`.

### 7.15 Resume and inspect safely
- An interrupted import keeps a staging directory and resumes when the identical command is rerun; do not change input files or mappings between attempts. A failed training run is not registered; fix the problem and rerun.
- `ml list datasets` lists snapshots; `ml show "$POLONY_SNAPSHOT"` prints the manifest; `ml list models` lists candidates and the active model.
- Never use `--allow-small`, `--allow-unconfirmed-identity`, an acknowledgement flag or a replaced test lock merely to silence a warning; each changes what can be concluded and is recorded in provenance. Keep the exact Git commit, mapping files, snapshot ID, test-lock checksum, candidate ID and comparison output with the experiment record.

## 8. Short form using the runbook script
[`scripts/runbook/real_training.sh`](../../scripts/runbook/real_training.sh) wraps the same stages. First read and set its `BASE`, `D`, `W`, `DATA`, `DEVICE` and GPU installation variables. One stage at a time; replace `<...>` with IDs printed earlier:

```bash
export BASE=/data/polony-training
bash scripts/runbook/real_training.sh install
bash scripts/runbook/real_training.sh upload
bash scripts/runbook/real_training.sh templates
bash scripts/runbook/real_training.sh mapping
# Edit and verify the generated mappings here.
bash scripts/runbook/real_training.sh preflight
bash scripts/runbook/real_training.sh dryrun
bash scripts/runbook/real_training.sh import
bash scripts/runbook/real_training.sh verify <snapshot-version>
bash scripts/runbook/real_training.sh split <snapshot-version>
bash scripts/runbook/real_training.sh lock <snapshot-version>
bash scripts/runbook/real_training.sh smoke
bash scripts/runbook/real_training.sh traindry <snapshot-version>
bash scripts/runbook/real_training.sh bench <snapshot-version>
bash scripts/runbook/real_training.sh train <snapshot-version>
bash scripts/runbook/real_training.sh eval <candidate-id>
bash scripts/runbook/real_training.sh compare <candidate-id>
```

The script does not promote; use section 7.14 after reviewing the comparison.

## 9. Alternative source: corrections reviewed in the app
Installation and 7.8–7.15 stay the same; replace 7.3–7.7 with a snapshot built from reviewed analysis IDs (run with `--dry-run` first, then repeat without it):

```bash
ml build --analyses ANALYSIS_ID_1 ANALYSIS_ID_2 ANALYSIS_ID_3 \
  --identity-map "$POLONY_WORK_DIR/reviewed-identities.json" --downscale 4 \
  --normaliser valid_unsaturated --fractions 0.7,0.15,0.15 --require-finalized --dry-run
```

The identity file is JSON keyed by analysis ID ([FINE_TUNING.md](FINE_TUNING.md#2-build-a-snapshot--build)). Same rules: only eligible reviewed regions become crops, groups must be independent, the locked test set is never trained on.
Copying a checkpoint directory alone does not register or activate it. The repository's `artifacts/` directory is an evidence bundle, not an installed model or a complete training dataset.
