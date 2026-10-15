# Fine-tuning Spotiflow from reviewed corrections

> Status and what is connected to the application: [STATUS_AND_RESULTS.md](../STATUS_AND_RESULTS.md).
> Start with [TRAINING_GUIDE.md](TRAINING_GUIDE.md) (fields, splits, training loss, the larger run recorded on 15 October 2026). This page is the technical guide for app-reviewed corrections.

Every step is explicit: the app never trains, evaluates, or promotes a model by itself. Code: `src/polony_app/ml/`. CLI: `python -m polony_app.ml <command>` (`--data-dir` defaults to the app's data directory / `POLONY_DATA_DIR`). Neither engine is ground truth; the only labels are the *human-reviewed final points*, with the reviewer's biases (see Limitations).

> **Earlier small-data experiment (not the larger saved run).** A leave-specimen-out sanity experiment (÷4, 10 epochs, from `general`) showed **no evidence that fine-tuning beat the pretrained model at the same threshold** (F1 within −0.03 … +0.02). Training on 2–3 slides was **unstable** (validation loss diverged after epoch 1 in one fold). The pipeline that produced those models also **trained at the wrong scale (native, not the inference downscale) and with a different normalisation** (per-crop instead of page-level percentiles); the normalisation difference alone moved recall by 0.2–0.4, far more than fine-tuning did. Both defects are fixed below. Any claim that a fine-tuned model generalises needs a leave-one-slide-out evaluation with the corrected pipeline (every slide held out once, same threshold, same configuration). Until then a candidate is a hypothesis, `train` refuses very small training sets, and promotion refuses configuration mismatches.

```
reviewed analyses ──build──► immutable dataset snapshot ──split/--lock-test──► locked test set
                                   │                                              │
                                   └──train (candidate)──► registry ──eval-model──┤
                                                              └── compare ── promote / rollback (explicit)
```

> **Historical ImageJ-annotated TIFFs** (~1,500 files): [LEGACY_FINETUNING.md](LEGACY_FINETUNING.md) (`ml import-legacy`: only fields the researcher examined, explicit channel/identity mapping, ROCm `gpu-smoke`, dry-run scale numbers). The `train` options added there (`--device rocm`, `--num-workers`, `--load-mode`, `--max-val-crops`) apply to every snapshot.

## 1. Collect corrections
Review analyses as usual. A region is **fully reviewed** only when a person approved it and nothing changed since (the approval fingerprint still matches). Colour/page comes only from a **confirmed channel mapping**; without it an analysis yields no crops.

## 2. Build a snapshot — `build`
```
python -m polony_app.ml build --analyses <id> <id> ... [--seed 0] [--fractions 0.7,0.15,0.15] [--identity-map ids.json]
                              [--allow-unconfirmed-identity] [--allow-bbox] [--strict-reviewed] [--require-finalized] [--dry-run]
                              [--downscale 1|2|4|8] [--normaliser valid_unsaturated|none]
```
`--downscale` and `--normaliser` define what the network sees and are part of the snapshot (options, every crop record, version hash). Use the downscale you run the model with in the app (large blobs: 2/4/8). Exported crops stay at **native resolution** (provenance); `train` and `eval-model` downsample on the fly.

It writes `<data_dir>/datasets/<version>/` (read-only, never overwritten). `version = ds-` + hash of the manifest content, which lists the sha256 of every file: identical inputs give an identical version and byte-identical files. Creation time and app version are recorded but not hashed.

| file | content |
|---|---|
| `manifest.json` | version, created, app version, options/seed, source analyses (+ TIFF sha256, review status, **reviewer identity** from the action log else `unknown` with a warning, engine/model versions of the source runs, channel mapping **only if confirmed else null**, alignment), crops (box in the stored page and in the reference frame, counts, sha256), skipped crops, label counts (incl. **unmarked raw proposals**, below), split assignment, test-lock reference, warnings, **unresolved assumptions** |
| `points.csv` | every point with `status`: `confirmed`, `human_added`, `rejected`, `unresolved`, `unreviewed`, `raw_proposal` (+ engine, model score, consensus status, page, role, split, crop id). x = column, y = row, pixel centres at integer coordinates |
| `regions.jsonl` | every region (counting/exclusion, polygon, approved, fully reviewed, rectangular, crop or skip reason per page) |
| `spotiflow/{train,val,test}/<id>.tif` + `<id>.csv` | crops cut from the **original page** (original dtype, no 8-bit conversion, no rescaling, single page, uncompressed) and their labels (columns `y,x`, crop coordinates) |

### Scale and normalisation (identical at training, evaluation and in the app)
* **Page-level lo/hi.** For each source page, lo/hi are computed **once**: percentiles 1 / 99.8 of the pixels of the *whole page* inside the app's valid mask (counting regions minus exclusions; green also minus the strip the alignment shift does not cover) **and not saturated** (below the dtype maximum). The same lo/hi applies to **every crop of that page**: `x_norm = (x − lo)/(hi − lo)` (not clipped). They are stored per source page in `manifest.json` (`sources[].page_normalization.<role>`: `lo`, `hi`, pixel counts, saturated count, fallback if any) and on each crop (`norm_lo`, `norm_hi`). This equals the app's `valid_unsaturated` normaliser, so training and inference see the same intensity scale. (The first version's per-crop percentiles put p99.8 at 5–10k where the page-level value is 38–65k.) `ml/common.py` computes them (pure numpy; training does not import the engine adapter) and a test pins them to the adapter's helper.
* **Downscale.** With `d > 1` the crop is block-mean downsampled on the page-wide block grid (the top/left remainder up to the grid and the bottom/right remainder are trimmed; nothing is padded). Labels map with the exact pixel-centre rule `x_s = (x − (d−1)/2)/d` (back: `x = x_s·d + (d−1)/2`). Labels in the trimmed remainder are dropped and counted.
* A snapshot built by an earlier version has crops without lo/hi: `train` and `eval-model` refuse it. Rebuild it and re-lock the test set with `--replace-lock --reason`.

Rules:
* **Positives** = objects a human confirmed, moved, reclassified or added. In a region the human *approved*, untouched proposals count as confirmed (approval attests they are the final set; basis `region_approved`). `--strict-reviewed` turns this off: such points become `unreviewed` and the crop is skipped. Rejected, unresolved and unreviewed points are **never** positives. Raw engine proposals are listed, never positives.
* **Crops** only from rectangular, fully reviewed regions (fields). A crop is skipped (with a warning) if it overlaps an exclusion region, contains an unresolved point (unlabelled real spots would teach the model that spots are background), is smaller than 32 px, or leaves the stored image. Non-rectangular regions are skipped unless `--allow-bbox` (the bounding box is cut; spots outside the polygon are unlabelled, with a warning).
* Green is aligned to red by an integer shift: its crop box and points are mapped back to the **stored page** (`box_xyxy` vs `box_reference_frame`).
* **Annotation incompleteness.** Precision against these labels is *precision vs this annotator's marks*: a real polony nobody marked looks like a false positive. When raw engine proposals are available, the manifest reports `label_counts.unmarked_raw_proposals`: proposals inside the exported crops with no annotator mark within 5 px, and how many are *bright* (score at least the lower quartile of the confirmed proposals; the score is a heatmap value, not a probability). A large count means incomplete labels (training on them teaches the model that those spots are background).
* The tool uses the app store read-only (`open_store`). Raw engine proposals and engine/model versions need `get_engine_runs/get_raw_detections`; if the store lacks them, the snapshot says so in its warnings.

## 3. Splits and the locked test set — `split`
Crops inherit the split of their **analysis**. Analyses are grouped specimen → slide → source file with `legacy_import.splits` (replicates of one specimen stay together; byte-identical files tie groups). Identity comes from, in order: `--identity-map` (confirmed); the slide id typed in the app (`<sample>_<replicate>`, specimen derived by that lab convention, listed as an assumption); the file name (**inferred, refused** unless `--allow-unconfirmed-identity`, which is recorded). Deterministic for a seed. With too few independent groups a split stays empty (never filled from the same slide) and the snapshot says so.

Print the group → split table, then lock the test set:
```
python -m polony_app.ml split --snapshot <v>
python -m polony_app.ml split --snapshot <v> --lock-test
```
`--lock-test` writes `<data_dir>/datasets/test_lock.json` (test group ids, specimen/slide/file keys, the test snapshot version, the hash of its test files). From then on:
* every later `build` puts analyses of a locked specimen/slide, or with identical file bytes, into **test only**, does **not** re-export them from the live analysis, and copies the locked test crops verbatim from the locked snapshot (hash-checked), so new corrections never change test labels;
* no new test groups are created (the test fraction moves to train/val);
* `train` **refuses** any snapshot whose train/val crops belong to a locked group or file;
* re-locking needs `--replace-lock --reason "..."` and is logged.

## 4. Train a candidate — `train`
```
python -m polony_app.ml train --snapshot <v> --base general|<registry id>|<model folder> [--epochs 30] [--lr 1e-4] [--batch-size 4]
                              [--crop-size 256] [--seed 0] [--device cpu|auto|cuda|mps] [--dry-run]
                              [--allow-small] [--min-train-groups 4] [--min-train-crops 20]
```
* **Trained at the snapshot's configuration.** Images are normalised with the page lo/hi and downsampled by the snapshot's `downscale`; Spotiflow's own per-image normalisation is off (`normalizer=None`). The registry entry records `inference_config` = `{downscale, normaliser}`, the lo/hi policy and the per-page lo/hi. `resolve_model()` returns this configuration (`ModelRef.inference_config`, `.trained_downscale`, `.config_warning(downscale, normaliser)`) and the training/evaluation/promotion CLI checks it. The app runs a fine-tuned model with this downscale and normaliser (overriding the UI settings for that model) and its saved threshold; see section 6.
* **Small-data safeguard.** `train` **refuses** (unless `--allow-small`, recorded as a warning in the entry) when the training split has fewer than 4 independent groups or fewer than 20 crops.
* **Best epoch is registered, last epoch is reported.** The weights are Spotiflow's `best.pt` (lowest validation loss). `metrics.training` holds best-epoch and last-epoch validation loss, the curve and a `diverged` flag (last > 1.25 × best, or not finite), with a warning. If `best.pt` is missing and the loss diverged, `train` refuses instead of silently registering `last.pt`.

`--dry-run` validates snapshot integrity, the lock, train/val crops, hyper-parameters and the base model, then stops. Training is refused without valid train **and** validation crops.

Fine-tuning continues from the base weights: `Spotiflow.from_pretrained/from_folder(..., inference_mode=False)` then `fit(...)` (what `spotiflow-train --finetune-from` does). Official pretrained names are downloaded by Spotiflow on first use. The result goes to `<data_dir>/models/<id>/` and the registry with status **candidate**: base model, dataset version, split membership (crop ids and groups), hyper-parameters, seed, duration, hardware, validation losses, weights sha256. A candidate is not used for detection until promoted or chosen by id. Defaults (CPU, lr 1e-4, 30 epochs) are starting points, not tuned values.

## 5. Evaluate on the locked test set — `eval-model`, `compare`
```
python -m polony_app.ml eval-model --model <id|general> [--tolerance 10] [--downscale d] [--normaliser m]
python -m polony_app.ml compare --models A B
```
`eval-model` runs the model on the locked test crops **at the model's own configuration**: a fine-tuned model uses the downscale/normaliser it was trained with (a different `--downscale` is refused); an official pretrained model uses the `--downscale` you name (default 1, recorded). It stores precision/recall/F1/matching distance at 5, 10 and 15 px in the registry, tied to the lock hash **and the configuration**. Predictions are mapped back to native pixels before matching. Evaluate the candidate **and** the model it would replace (the active one, else `general`). `compare` shows them side by side. Results are labelled `preliminary` when thin ([EVALUATION.md](EVALUATION.md)).

## 6. Promote / roll back — explicit
```
python -m polony_app.ml promote <id> [--app-downscale d] [--app-normaliser m] [--acknowledge-config] [--force --reason "..."]
python -m polony_app.ml rollback
```
`promote` requires evaluations of the candidate and of the model it replaces on the **current** lock, each **at its own recorded configuration** (a pretrained baseline: the app's current configuration), and refuses a candidate with lower F1 (at 10 px). It also refuses when the candidate's configuration (downscale, normaliser) differs from the **app's current inference configuration** (`--app-downscale`, `--app-normaliser`; default: the app's default Spotiflow settings) unless `--acknowledge-config`; then the analyses must be run at the model's downscale. `--force --reason "..."` overrides everything and is recorded. `rollback` restores the previously active registry entry (or no promoted entry).

**Use in the app.** The Spotiflow model setting defaults to `active`: the promoted model, or pretrained `general` when none is promoted. After `promote`, normal app detection uses the promoted model. A registry candidate can also be chosen by id in the model picker or API. The model runs with its trained downscale and normaliser and its own saved threshold. The run record names it by registry id and keeps the weights checksum. The app uses a model only where the registry and `models/<id>` weights are in its data folder.

The CLI resolves model names with `polony_app.ml.registry.resolve_model(name, data_dir)`: a registry id → its weights folder (sha256 re-checked), `"active"` → the promoted model, anything else → an official pretrained name. Promotion procedure and evidence: [TRAINING_GUIDE.md](TRAINING_GUIDE.md#714-promote-only-after-accepting-the-evidence).

## Hardware
CPU is the default and enough for small correction sets (the opt-in test fine-tunes a tiny model for 2 epochs in about a second). Pretrained-size models on many crops are slower on CPU; `--device auto` uses CUDA/MPS when present. Hardware and library versions are recorded per model.

## Limitations
* **One annotator / one session** is the usual case: labels reflect that person's choices and fatigue; model gains can be bias learnt, not accuracy. Annotator count is read from the action log, else `unknown`.
* **Unlabelled areas**: only fully reviewed fields are cropped, but a human can still miss real spots inside them; those become false "background".
* Approved regions with untouched proposals are accepted as confirmed (`--strict-reviewed` avoids this at the price of fewer crops).
* The page-level normalisation matches only the app's `valid_unsaturated` normaliser; analyses run with the legacy `auto` normaliser see a different scale than the model was trained on.
* A model trained at ÷d is only valid at ÷d. Its localisation accuracy is about ±d/2 px, so evaluate with a tolerance that allows for that (10–15 px).
* Training sets of a few slides are unstable (see the note at the top).
* Few groups ⇒ small, noisy test set; metrics are `preliminary`. Nothing here proves a fine-tuned model generalises to new scanners or samples.
* The researcher's reference marks (ROI) are not training labels here; only app-reviewed points are.
* **Never auto-train**: no scheduler, hook or background job. A person runs each step.
