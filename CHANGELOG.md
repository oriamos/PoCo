# Changelog

All notable changes to PoCo / Polony Review are recorded here. The project follows [Semantic Versioning](https://semver.org/)
from 0.1.0; while the major version is 0.x, minor releases may change behaviour and file formats, and the release notes say so.

## 0.3.3 — the AI detector installs on Apple Silicon Macs with an Intel Python, and on Intel Macs (2026-10-20)

### Fixed

* **Installer: an Intel (x86_64) Python on an Apple Silicon Mac** (for example an Intel miniconda running under Rosetta) was mistaken for an Intel Mac, so
  PyTorch was not installed and the AI detector failed with `No module named 'torch'`. On Apple Silicon, `install.sh` now skips Intel Pythons (also in an
  existing environment) and downloads a native arm64 Python 3.12 with `uv` when none is found, so current PyTorch and the Apple GPU (MPS) are used.

### Changed

* **No approval step.** Every counting region (selected grid field) counts as confirmed: the "I inspected this region" tick and the Approve / Unapprove
  buttons are gone, and Finalize no longer asks for them. "Accept all proposals" works without the tick. Save and Finalize mark the regions inspected and
  approved automatically, so exports and training data keep their flags. The grid can be cleared or re-applied at any time (it was refused while a field was
  approved). The `approve_region` / `unapprove_region` / `region_inspected` actions still exist in the API.
* **Save: one CSV row per colour, with a `Color` column.** Ticking red only, green only and yellow now gives a row for each (before, ticking several colours in one line
  merged them into one combined row). `<name>.csv` is now `SlideID, Color, Total number of polonies, Field1 ... Field24` with one row per colour, in one file
  (no more `<name>__<colour>.csv`). Combined rows (red + yellow, green + yellow together) are separate optional ticks. `experiment_counts.csv` keeps its columns
  (`What counted` names the colour there).
* **Save: "Choose folder and file name…" button** (desktop window): opens the system save window, where the researcher picks the folder and types the
  file name (used for `<name>_labeled.tif` and `<name>.csv`; the "Slide name" in the CSVs stays the scan's name). In the browser the folder is still typed.
* **CSV: counted grid fields are listed one by one.** `Field1, Field2, ...` are the counted fields in grid order, whatever their numbers in the grid are
  (a switched-off field no longer leaves a blank column; grid numbers above 24 are fine as long as at most 24 fields are counted). The labelled scan keeps
  the grid numbers.

### Added

* **AI detector on real Intel Macs:** installs PyTorch 2.2.2 / torchvision 0.17.2 (the last releases published for Intel Macs) with `numpy<2`; CPU only, slower.
  Not yet tested on Intel hardware.

## 0.3.2 — one-click rejection of debris-like Big-FISH-only candidates (2026-10-19)

### Added

* **Review tab: "Reject N debris-like Big-FISH-only candidates".** One undoable `delete` of every unreviewed automatic candidate that only
  Big-FISH found and that is also `debris_like` (97 % had no researcher mark on 7 research slides: 333 of 345, against 18 % of the other
  Big-FISH-only objects). It is a reviewer action recorded in each object's history (`delete` now accepts an optional `note`); nothing is
  removed automatically. Helpers: `review/counts.is_debris_speck`, `debris_speck_candidates`; `lib/consensus.debrisSpeckIds` in the UI.

## 0.3.1 — terminal update and a usable default grid (2026-10-19)

### Added

* **`polony-review update`** (macOS, Linux, Windows via `python -m polony_app.launcher update`): updates an installation in place from the terminal.
  It picks the newest release (or `--ref`), checks that release's installer against `SHA256SUMS.txt`, and runs it; only changed code is fetched,
  installed libraries (including the AI detector), settings and data are kept. `--check` only reports whether a newer release exists; `--force` reinstalls.
  The command first exists in this release, so v0.3.0 installations update once with the install command from the README.

### Changed

* **New PoCo logo** (red and green circles with a yellow overlap): app icons (Windows, macOS, Linux), the top bar, the browser tab icon and the README.

### Fixed

* **Grid fields: Apply and Randomise were disabled out of the box.** The default grid had 28 cells (4 x 7) but the lab template ends at field 24, so both
  buttons were blocked and the picking mode (click fields to count them) never opened. The default is now 4 x 6 = 24 fields and the message
  says to reduce rows x columns to 24 or fewer. Slides whose grid has 28 physical cells still count at most 24 fields (open question in
  `docs/app/SCIENTIFIC_OPEN_QUESTIONS.md`).

## 0.3.0 — the AI install ships the fine-tuned model (2026-10-16)

### Added

* **A fresh AI install downloads and uses the fine-tuned model** `ft-7e4c89cb-8edc09e3` (downscale 4, `valid_unsaturated`, threshold 0.3).
  The files are assets of the GitHub Release `model-ft-7e4c89cb-8edc09e3` (built by `.github/workflows/model-release.yml` from a pinned commit,
  checksummed, with the Spotiflow BSD-3 notice). The laboratory approved distribution (recorded from Ori Amos).
* `polony_app.ml.bundled_model`: atomic download, size and SHA-256 check against pinned values, reuse on repeat installs; shared by the
  Windows, macOS and Linux installers through `install/ai_extra.py` (`ai_extra.py model` retries; `POLONY_BUNDLED_MODEL=0` opts out).
  A failed download never fails the AI install.
* `Registry.register_bundled`: an explicit, logged registration (`origin: bundled`, no invented evaluation). It activates the model only
  when none is active and never changes existing models, the active model or a rollback. Promotion of user-trained candidates still
  needs locked-test evidence.
* `install/ci/smoke_model.py`: real inference with the shipped checkpoint through the app's default path, run by the AI install check on all three platforms.

### Not changed / open

* The licence of the upstream pretrained Spotiflow weights has no separate statement; confirmation from the authors is outstanding
  ([MODEL_CARD.md](MODEL_CARD.md)). The original registry entry is not published; its fields are not verified here.
* The model's results are agreement with saved marks, not accuracy; it over-counts more than the pretrained model.

## 0.2.0 — the application uses the promoted model (2026-10-15)

### Changed

* **App detection uses the fine-tuned model.** The Spotiflow model setting now defaults to `active`: the promoted model of the model
  registry, or the pretrained `general` model when none is promoted (no change without a promoted model). After `promote`, normal
  detection uses it. A registry candidate can also be chosen by id. The model picker lists the promoted model, the pretrained models
  and the registry candidates. A fine-tuned model runs with the downscale and normaliser it was trained with and its own saved
  threshold; the run record names it by registry id and keeps the weights checksum. A model whose weights are missing or modified is
  refused with a clear message. The weights themselves are still not part of the repository.
* The guides were rewritten shorter: a short explanation and the terminal commands. `docs/app/TRAINING_GUIDE.md` starts with a
  "Quick path". No commands, numbers or caveats were removed.
* Installers, README and `docs/app/INSTALL.md` install `v0.2.0` by default; `constraints/release-0.2.0.txt`.

### Fixed

* The `install-test` uninstall check failed whenever the optional AI extra had been installed: the uninstaller keeps the downloaded
  AI models by design, so `~/PolonyReview/models` remained and the check expected the whole folder to be gone. The check now accepts a
  remaining folder only if it holds nothing but `models` and the AI extra was installed. No installer behaviour changed.

## 0.1.0 — first public release (research stage)

First release under the repository `oriamos/poco`. The history before this release was re-based into a clean initial commit; see
[NOTICE](NOTICE) for the origin of the project and [AUTHORS.md](AUTHORS.md) for who did what.

### Added

* Demo path: `make demo` runs the app on a synthetic two-channel slide in its own folder; `make demo-reset` removes it. See [TRY_DEMO.md](TRY_DEMO.md).
* Automated smoke test for the demo path (`tests/app/test_demo_smoke.py`).
* [docs/STATUS_AND_RESULTS.md](docs/STATUS_AND_RESULTS.md): one page separating the eight-slide exploratory evaluation, the larger
  saved-data fine-tuning run and the application integration status.
* [MODEL_CARD.md](MODEL_CARD.md) for the fine-tuned Spotiflow candidate, including the redistribution status of its weights.
* Public project files: [CONTRIBUTING.md](CONTRIBUTING.md), [SECURITY.md](SECURITY.md), [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md),
  [CITATION.cff](CITATION.cff), [NOTICE](NOTICE), [AUTHORS.md](AUTHORS.md), and issue and pull-request templates.
* [docs/REPRODUCIBILITY.md](docs/REPRODUCIBILITY.md) and `constraints/release-0.1.0.txt`: what can and cannot be rerun, and the exact
  dependency versions tested for this release.
* CI: a Python 3.10 / 3.11 / 3.13 smoke matrix, an install with the release constraints on 3.12, and a Markdown local-link check
  (`scripts/check_markdown_links.py`).
* Release workflow (`.github/workflows/release.yml`): creates the GitHub Release with notes from this file, the installer scripts and
  `SHA256SUMS.txt`, either when a `vX.Y.Z` tag is pushed or when started by hand with a version (it then creates the annotated tag, and
  refuses a commit whose other checks are not all green).
* Dependabot (`.github/dependabot.yml`) for pip, npm (minor and patch only) and GitHub Actions; `NOTICE` lists the licences of the Python dependencies read from package metadata.
* The installers print the installed version and where it came from, and their usage comments show the release-tag command.
* The demo test also opens the slide in place, generates a grid, detects and saves, and asserts the three output files.
* Installers install the tagged release `v0.1.0` by default; `POLONY_REF=main` selects the development branch. Tags are downloaded
  from `refs/tags`. The installers do not check SHA-256 checksums yet (planned; see [SECURITY.md](SECURITY.md)).

### Changed

* The application and documentation use the name **PoCo / Polony Review** (the header previously read "Polony Counter").
* The root README was rewritten: what the application does, the workflow, the demo, the install commands for the release tag, and
  the scientific limits.
* Repository references point to `oriamos/poco`.
* The version in `pyproject.toml` is 0.1.0, matching the application (`polony_app.__version__`) and the frontend package.
* `CODE_OF_CONDUCT.md` is the official Contributor Covenant 2.1 text.
* Documentation no longer calls the eight-slide evaluation "validation", and notes that numbers quoted for `test_img` belong to an
  earlier real image that is no longer distributed (the shipped file is a synthetic stand-in).
* The User Guide screenshots and the README hero image were re-captured from the synthetic demo slide with the current name.
* Hard-coded test counts were removed from the documentation; the CI badges show the current result.

### Fixed

* The E2E check "zoom about cursor keeps image point fixed" was flaky on CI (it measured drift of 0.3 image px against a 0.2 px
  tolerance). The check now anchors the zoom on whole pixels and allows one readout unit (0.1 px). A deliberately broken zoom is
  caught by the check.

* GitHub Actions use `actions/checkout`, `setup-python` and `setup-node` v7 (the CI showed a Node.js 20 deprecation warning for v4).
* The detection pipeline (`src/polony_app/detection/pipeline.py`) did not compile on Python 3.10 and 3.11: one f-string nested the same
  quote character, which needs Python 3.12. The Big-FISH engine therefore could not be imported on those versions even though
  `pyproject.toml` and the installers accept 3.10-3.13. Found by the new Python smoke matrix; the message text is unchanged.
* The Windows installer check hung until the 40-minute job timeout, so every earlier `install-test` run ended as "cancelled", not
  as pass or fail. Cause: `check_windows.ps1` started the launcher with `Start-Process -Wait`, which also waits for the server the
  launcher leaves running in the background. The check now waits for the launcher process only, and the Windows launch, relaunch and
  uninstall steps have a 10-minute step timeout, so a hang fails visibly.

### Removed from the repository

* The fine-tuned checkpoints (`best.pt`, `last.pt`) are not included. Their redistribution rights are not verified; see
  [MODEL_CARD.md](MODEL_CARD.md) and [artifacts/README.md](artifacts/README.md). Their SHA-256 values are recorded in
  [MODEL_CARD.md](MODEL_CARD.md). The registry record itself is not published (it names laboratory slides).
* The full snapshot manifest of the historical training data is not included, because it lists unpublished laboratory file names.
  The lock file is kept.
