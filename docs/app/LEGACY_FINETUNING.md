# Fine-tuning Spotiflow on the historical ImageJ-annotated TIFFs
Operator guide for `python -m polony_app.ml import-legacy`: ~1,500 historical two-page TIFFs with embedded ImageJ marks enter the **same** snapshot -> split -> lock-test -> train -> eval-model -> compare -> promote lifecycle as reviewed analyses ([FINE_TUNING.md](FINE_TUNING.md)): page-level `valid_unsaturated` normalisation, block-mean downscale, exact coordinate mapping, content-addressed snapshots, locked test set. This is **fine-tuning** of pretrained Spotiflow (`--base general`), not training from scratch. Status and what is connected to the application: [STATUS_AND_RESULTS.md](../STATUS_AND_RESULTS.md). New to training? Read [TRAINING_GUIDE.md](TRAINING_GUIDE.md) first; counts in section 2 describe the earlier eight-file dry-run, not the full dataset.

> **What the marks are.** One person's clicks (median ~5-6 px from the intensity peak), not ground truth. A missing mark is **not** a negative (the file cannot tell "examined, no polonies" from "not examined"). Every metric is *agreement with this annotator*.
## 1. The rule: only fields the researcher examined, per (TIFF, field, page)
A crop is exported only with **explicit evidence that the researcher examined that exact TIFF, grid field and page**. Eligibility is decided independently per `(TIFF, field, page)`: marks on page 0 never make page 1 eligible. No marks does not mean zero.

| status | evidence | training use |
|---|---|---|
| `positive_marked` | embedded ImageJ marks on **that page** inside **that field** | crop with its marks as labels |
| `verified_zero` | explicit sidecar/manifest entry: researcher counted that field on that page, count 0 | crop with empty label file |
| `unknown` | no marks, no explicit record (grid overlay, marks on the other page, application detections are **not** evidence) | **excluded**, never a negative |
| `conflict` | stated count disagrees with the marks (or stated zero with marks) | **excluded** and reported |

* `--mode`: `marked-only` (default; field/pages with at least one mark) or `examined-fields-manifest` (only tuples in `--examined-fields`; verified zeros allowed). No "all cells negative unless marked" mode exists.
* Stray points (ImageJ counter belongs to another cell) are not evidence for the cell they fall in: excluded and recorded. A mark with no usable plane (position missing, 0 or beyond the planes) is evidence for no page: all field/pages of its cell become `conflict` (`plane_out_of_range`).
* A mark belongs to the crop whose integer pixel footprint contains its rounded centre (`floor(x + 0.5)`), for evidence, labels and counter->cell mapping, so a mark at a grid line is never background in one crop and a label in another.
* Never labels: out-of-bounds, duplicate, outside-grid, untrained-page, unspecified-plane or non-examined-cell points. They appear as `dropped:<reason>` in `points.csv` and in the manifest counts. Nothing is clamped.
* Each crop carries `provenance` (`researcher_examined: true`, `examination_source`, `evidence`, TIFF + sha256, page, `imagej_position`, channel role and mapping source, counters, grid row/col/polygon, positive-marked or verified-zero, mark count, coordinate frame, assumptions). `train` refuses crops lacking `researcher_examined == true`. The app's researcher-comparison report follows the same rule (unknown fields excluded from totals, MAE, slope, r): [FIELDS.md](FIELDS.md).

## 2. What the real files showed (differences from the working assumptions)
Measured on 8 extracted research files (7 two-page stacks + 1 RGB composite) plus `test_img.tif`; reproduce with `import-legacy --dry-run`. Not identical to the 8 raw slides of [REAL_DATA_VALIDATION.md](REAL_DATA_VALIDATION.md) (which also has 7 RGB composites).
* Confirmed: two-page `uint16` ImageJ stacks (ZYX), 2438x1460 (`test_img` 2450x1438); ROI = one POINT blob with counters and positions; counter = **field**, not class; ImageJ position 1/2 = page 0/1; overlay = 28 cells of ~316.23 px. The eighth file is an 8-bit RGB composite (LZW, blue plane = saturation mask): rejected as `unsupported_layout`. No `AI-A` raw stack in this set.
* `FS-B_D` was counted on a shifted grid and its stored overlay is that grid (origin (3, 123), ~(-158, -34) from the (158, 158) origin of the others; on (158, 158) its counters would span 3-4 cells). The bridge always uses the file's own overlay. Counter oddities: `AI-B` three counters with a point one cell over, one point 1.5 px outside the grid, counter 12 a second out-of-order counter; `AS-B` counter 11 out of order; `AM-B` counters 3, 19 absent (lab CSV numbers fields without gaps, so "field = counter + 1" **fails after counter 19**); `AS-A` counter 7 absent.
* Page 1 has marks in only 4 of 7 stacks (13 field/pages: AI-B, AM-B, AS-B, FS-B_D, as the slice-2 points in REAL_DATA_VALIDATION.md; first three reproduce the 'Clade A' sheet), so page 1 is almost entirely `unknown`. Names say 29-09-2026, scanner metadata 2026/09/30; AI/AM/AS PMT 550 / laser 1.97, FS PMT 500 / 3.30. No scan-session id: `scan_session` stays empty unless supplied.
* `marked-only`, page 0 trained: **196 field/pages, 108 examined (all positive_marked), 88 excluded** (87 no marks, 1 only straddling points); 1,098 ImageJ points -> 1,078 labels, 20 dropped.

## 2b. Normalisation: the same mask the app uses
Page-level `lo/hi` (percentiles 1 / 99.8 of valid, unsaturated pixels) must use the app's inference mask, else training sees a scale the app never produces (examined-cell `hi` differs from whole chamber by 1.5-11x; chamber `hi` differs between slides, e.g. 3.4k to 44k). Only pixel statistics are used (no labels, no test set). `--valid-mask`:
* `chamber` (default): the app's automatic chamber (rim 40 px, all planes) as valid mask, computed once per source. No chamber: union of all grid cells with a recorded warning (`valid_mask_used` per page in the manifest). `grid-cells`: forces that union. `eligible-fields`: examined fields only; experiments, **not** inference parity.

## 3. Files you provide
`import-legacy --input DIR --write-templates OUT` writes all three as **templates** (reads no pixels; nothing in a template is confirmed).

### 3.1 Channel map (`channels.json`) - required for a real import
The researcher's statement of what each page shows; roles are never inferred from file names or the `635 [W1]` label.
```json
{ "schema": "polony-channel-map", "version": 1,
  "confirmed_by": "<who confirmed this mapping>", "confirmed_on": "2026-10-14",
  "source_of_truth": "<on what basis: protocol, scanner export, researcher's statement>",
  "defaults": { "pages": { "0": {"role": "red", "train": true}, "1": {"role": "green", "train": false} } },
  "rules": [ { "id": "fs-scans", "match": {"glob": "*_FS-*.tif"}, "pages": { "0": {"role": "red", "train": true} } } ],
  "files": { "some/dir/odd_file.tif": { "pages": { "0": {"role": "green", "train": true} } } } }
```
* Strict: unknown keys (e.g. `"trian"`) rejected; each page block states `role` **and** `train`; `files` keys are exact relative posix paths (`./x`, other case, backslash = error naming the nearest file). A rule or `files` entry matching no scanned file is a **blocker** (import refuses; dry-run lists it under BLOCKERS).
* Precedence `files` > `rules` > `defaults`; rule `match` keys: `glob`, `assay`, `sha256`, `specimen_id`, `slide_id`. Refused: two rules matching one file, page index beyond the planes, empty or duplicate role in a file.
* Empty `confirmed_by` or `source_of_truth` is refused. The template's default (page 0 `red` train, page 1 `green` not trained; validated on the research stacks) is active only once filled in. Origin (`default` / `rule:<id>` / `file`) is recorded per file. The dry-run prints an information-only check of the ImageJ `Info` label per file and lists deviations; it never decides a role.

### 3.2 Identity map (`identities.json` or `.csv`) - required for a split
```json
{ "rows": [ { "file": "29-09-2026_T7_AB_AM-A.tif", "specimen_id": "AM", "slide_id": "AM_A",
              "assay": "T7_AB", "replicate": "A", "scan_session": null, "confirmed": true } ] }
```
* `file` = path relative to `--input` (or unique base name); `confirmed` must be explicit (missing key or empty CSV cell is an error). `specimen_id` groups replicates into one split; required unless `--level slide`. Same specimen id (case-insensitive) with different `assay` is refused; `AM`/`am` merge with a warning.
* `confirmed: false` or unlisted files are inferred from names and **refused for splits** unless `--allow-unconfirmed-identity` (recorded in the manifest). Byte-identical files merge into one group.

### 3.3 Examined-fields manifest (optional; only for verified zeros) - `--mode examined-fields-manifest --examined-fields F.json`
```json
{ "schema": "polony-examined-fields", "version": 1,
  "evidence": "T7B_15-09-2026.csv: blank = not counted, 0 = counted zero (confirmed by <name> on <date>)",
  "source_kind": "sidecar_csv", "examined_by": "<name>", "recorded_on": "2026-10-14",
  "files": [ { "file": "29-09-2026_T7_AB_AM-B.tif", "pages": { "0": [ {"counter": 3, "count": 0}, {"row": 1, "col": 2, "count": 0}, {"counter": 5} ] } } ] }
```
* A field is named by `counter`, `field` (lab number; read as counter N-1 only with `--acknowledge-field-equals-counter-plus-one`) or `row`+`col`.
* `count: 0` (or `counted_zero: true`) = verified zero. No stated count and no marks stays `unknown`; a count differing from the marks is `conflict`. CSV form: `file,page,counter|field|row+col,count,counted_zero,note`, first line `# evidence: ...`.
* **Lab CSV caution:** gap-free lab numbering mislabels fields after an absent counter (`AM-B`, counter 19). `--lab-csv/--lab-series/--acknowledge-lab-csv-field-numbering` exist, but ambiguous entries go to `unresolved_manifest_entries`, never guessed. Prefer researcher-confirmed `row`+`col`.

## 4. Operator workflow for the ~1,500-file directory
Set `D` (historical TIFFs) and `W` (templates, reports). `--data-dir` = app data dir (snapshots in `<data-dir>/datasets`, models in `<data-dir>/models`). Nothing trains, locks or promotes by itself; no step asks a question.
```bash
M="python -m polony_app.ml --data-dir DATA"
# 1. Audit names/metadata (templates only): identities.template.json (inferred, confirmed:false), channels.template.json (unconfirmed), examined-fields.template.json
$M import-legacy --input $D --write-templates $W/tpl
# 2. (manual) Copy templates to identities.json / channels.json; check each identity row against lab records, set confirmed:true; fill confirmed_by, confirmed_on, source_of_truth (3.1); add rules/files for deviating files; optional examined-fields.json (3.3)
# 2b. Pre-flight (read-only, exit 0/1/2): cross-checks the scan independently
$M preflight --input $D --channel-map $W/channels.json --identity-map $W/identities.json
# 2c. Before trusting new code on the full set: synthetic rehearsal against an independent oracle (scripts/preflight/README.md; 143 checks at N=1500; ~30 min, ~1 GB RAM, 880 MB input; no real scanner data, no GPU speed)
PYTHONPATH=src python3 scripts/preflight/rehearsal.py --n 1500 --cell-px 64 --workers 4 --out DIR --keep
# 3-4. Import dry-run (writes nothing); review the report (section 5), fix mapping files, repeat until BLOCKERS is empty
$M import-legacy --input $D --channel-map $W/channels.json --identity-map $W/identities.json --downscale 4 --normaliser valid_unsaturated --fractions 0.7,0.15,0.15 --batch-size 4 --epochs 10 --dry-run
# 5. Immutable snapshot: --workers 4 writes crops concurrently (byte-identical for any count; interrupted run resumes)
$M import-legacy --input $D --channel-map $W/channels.json --identity-map $W/identities.json --downscale 4 --workers 4
$M verify <version>  # same input again prints "already imported as <version>" (exit 0, nothing rewritten; plan key in import_summary.plan_key, includes a hash of the import code, so a code update builds a new snapshot). Symlinks resolving outside --input are never followed (listed as skipped)
# 6. Inspect, then lock the test split (too few independent groups: split stays empty, never filled from the same specimen). The lock is permanent. Refused for snapshots built with an --acknowledge-* assumption (no counters, field = counter+1, lab-CSV numbering) unless --allow-acknowledged-assumptions-in-test-lock (recorded). Locked identities match case-insensitively on specimen+slide id WITHOUT assay; train refuses train/val sharing one. Later builds carry locked crops over; train refuses locked material
$M split --snapshot <version>
$M split --snapshot <version> --lock-test
# 7. ROCm GPU smoke test (cuda, rocm = alias, auto all mean the ROCm GPU via torch.cuda): versions, device, memory, matmul+backward, conv2d, gradients vs CPU. If torch.version.hip is set but no device is visible it lists what to check (/dev/kfd, video/render groups, gfx target, HSA_OVERRIDE_GFX_VERSION). An explicit GPU never falls back to CPU silently (--device auto may, with a notice)
python -m polony_app.ml gpu-smoke --device rocm
# 8. 1-epoch benchmark; run train ... --dry-run first (prints actual scale). Total = s/epoch x epochs + validation each epoch + twice more for threshold optimisation
$M train --snapshot <version> --base general --device rocm --batch-size 4 --epochs 1 --num-workers 4
# 9. First candidate: BEST validation checkpoint registered (last epoch only reported), as a candidate, never active. --num-train-samples N bounds an epoch (draws with replacement)
$M train --snapshot <version> --base general --device rocm --batch-size 4 --epochs 10 --early-stopping-patience 3 --num-workers 4
# 10. Evaluate candidate and general on the same locked test set
$M eval-model --model <candidate-id> --device rocm
$M eval-model --model general --downscale 4 --device rocm
$M compare --models <candidate-id> general  # 11. precision/recall/F1 at 5, 10, 15 px, vs this annotator's marks
# 12. Promote only if evidence supports it (never on a thin or preliminary test set); refuses lower F1 or config mismatch; `rollback` restores the previous model
$M promote <candidate-id> --app-downscale 4 --app-normaliser valid_unsaturated --reason "..."
```
The app's Spotiflow model setting defaults to `active` (the promoted registry model, else pretrained general); after `promote`, app detection uses it with the model's own downscale, normaliser and threshold.

### What `--dry-run` of `train` prints (real numbers from your snapshot)
Sources with crops, eligible crops and train/val/test split, epochs, batch size, `num_train_samples`, steps per epoch, **estimated optimiser steps**, validation batches per pass and in total (batch size 1; plus 2 sanity-check batches and a final threshold optimisation over the validation set), in-memory size vs available RAM, load mode, native snapshot size, `Training will not start because --dry-run was supplied.`, and recommendations (1-epoch benchmark, then ~10 epochs with early stopping). Sample, 8 research files at downscale 4:
```
sources (source images): 8 in the manifest, 7 with crops
eligible crops: 108  (train 52, val 17, test 39 - locked/held out, never trained on)
epochs: 10   batch size: 4   downscale: 4   device: cpu   workers: 0
steps per epoch: 13   estimated optimizer steps: 130
validation: 17 batch(es) per pass x 10 pass(es) = 170 batches, + 2 sanity-check, + 34 for the final threshold optimisation
prepared in-memory size (float32 network inputs): 1.6 MiB; load mode: eager
```

## 5. Reading the import dry-run
`IMPORT-LEGACY DRY RUN` lists: **sources** (discovered / unique / accepted / rejected by reason / duplicates merged); **pages and channel mapping** with origins and the `Info`-label check; **field/page tuples** by status with the exact number **excluded because examination could not be proven** (`unknown` + `conflict`, with reasons); positives per page/role, **annotations not used as labels** by reason, **groups and splits**; **estimates** (native size, in-memory size, batches per epoch), identity table (inferred vs confirmed), `BLOCKERS`. It exits 0 even when a real import would be refused for identity/mapping gaps (printed as blockers); malformed mapping/manifest files exit 2.

## 6. Disk, RAM and time - how to size the real run
* **Disk:** native crops are uncompressed at original dtype, ~`h x w x 2` bytes (316x316 uint16 ~200 KB); 54,000 crops ~10.8 GB. The dry-run prints the exact estimate; the build refuses early if free space is clearly insufficient (10 % margin).
* **RAM:** float32 inputs after downscale `d`: ~`(316/d)^2 x 4` bytes per crop (d=4 ~25 KB; d=1 ~400 KB); 54,000 crops ~1.3 GB at d=4, ~21 GB at d=1. Above 8 GiB (or 25 % of free RAM) `train` switches to bounded lazy loading (`--load-mode`, bit-identical to eager), or refuses an explicit `eager` that does not fit unless `--allow-large-memory`.
* **Time:** CPU smoke benchmarks only (`scripts/benchmarks/ml/`): eager vs lazy overhead ~0-12 %; `eval-model` ~0.15-0.44 s per crop on 4 cores (8,000 test crops ~20-60 min). Predictor batching measured, **not adopted** (identical predictions, no consistent speed-up). Use the 1-epoch benchmark for real seconds/epoch.
* **Validation cost:** batch size 1 (a `--val-batch-size` would change metrics). `--max-val-crops N` (deterministic subset ordered by `sha256(crop_id)`, recorded) limits it. `--num-workers N` feeds train and validation loaders; different counts are not bit-identical (recorded in the registry entry).

## 7. Interface decision
The bridge is `ml import-legacy` (not a `dataset build` flavour or new training system): it produces the **same** snapshot format via the shared `assemble_snapshot`, so `verify`, `split`, `--lock-test`, `train`, `eval-model`, `compare`, `promote`, `rollback` are unchanged and keep every guarantee (content-addressed immutable snapshots with sha256 per file, atomic publication, deterministic output, grouped splits, locked test set, page-level normalisation, downscale/normaliser recorded in snapshot and registry). New: `manifest.import_summary` and per-crop `provenance`.

## 8. Robustness behaviour you may notice
* **Refusals, not tracebacks:** disk full, permission denied, source deleted/truncated mid-import, unwritable data dir end with `REFUSED: ...` (exit 2) naming path and OS reason; staging is kept so a rerun resumes. Ctrl-C is never swallowed.
* **Strict mapping files:** 8 MB and nesting limits; **duplicate JSON keys refused** (never "last wins"); unknown keys, wrong types, page keys other than 1-4 ASCII digits refused with the key. A channel-map `files` or manifest entry naming no scanned TIFF refuses the import (exit 2, also in `--dry-run`) with the nearest file name. **Non-UTF-8 file names** are skipped (`filename_not_utf8`), listed, never mangled into provenance.
* **Concurrency:** each staging directory is locked under `<data-dir>/.locks/`; the loser of a publication race gets `REFUSED: snapshot ... already exists ... published by another run`. After a publish, other `.staging-*` directories with a free lock are reclaimed, and any older than 7 days at import start. **A source changed during import is never exported with the old hash:** size, mtime, inode, ctime are re-checked and the file re-hashed when its first plane is read.
* **`verify` / `train` gates:** paths leaving the snapshot directory fail `verify` (exit 3). `train` refuses unknown split names, duplicate crop ids, impossible shapes, non-finite or non-increasing `norm_lo/norm_hi`, and any bridge import (`options.legacy_import`, non-empty `import_summary` **or** crop provenance) whose crops lack `researcher_examined == true`. Known gap: a manifest with all three markers deleted and re-sealed is indistinguishable from a snapshot of reviewed analyses.
