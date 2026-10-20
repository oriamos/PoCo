[![CI](https://github.com/oriamos/poco/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/oriamos/poco/actions/workflows/ci.yml)
[![Installers](https://github.com/oriamos/poco/actions/workflows/install-test.yml/badge.svg?branch=main)](https://github.com/oriamos/poco/actions/workflows/install-test.yml)
![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)

<p align="center"><img src="docs/app/img/poco-logo.png" alt="PoCo" width="360"></p>

# PoCo / Polony Review

**PoCo turns two-channel microscope TIFFs into reviewed red, green and yellow polony counts. Big-FISH and Spotiflow propose detections; a researcher reviews each counting field; the application exports lab-ready CSV/Excel files with full provenance.**
![PoCo application with a synthetic two-channel demo slide](docs/app/img/hero-demo.png)
*The screenshot shows the synthetic demo slide from `resources/dataset_files/test/`, not laboratory data.*

A **polony** is a small fluorescent spot made by amplifying a single DNA molecule on a slide. Each slide is scanned in two channels (colours). A spot only in the red channel is **red**, only in the green channel **green**, at the same place in both **yellow**. The counts per counting field are the result. **Who it is for:** researchers who count polonies (solid-phase single-molecule PCR spots) on fluorescence scans and want a reproducible, reviewable count instead of manual tallies alone. The app runs on your own computer and uploads nothing, unless you connect the optional shared database ([docs/app/SHARED_DATABASE.md](docs/app/SHARED_DATABASE.md)).

## The workflow
1. **Import** a two-channel TIFF (or two single-channel files).
2. **Map channels**: confirm which channel is red and which is green. File names only suggest a role.
3. **Choose fields**: generate the counting grid, click the fields to count, or randomise the grid (the seed is recorded).
4. **Detect**: Big-FISH (classical) and, optionally, Spotiflow (AI) propose spots in each field.
5. **Review and export**: review the counts, then export `experiment_counts.csv`, Excel workbooks in the lab's layout, and a provenance file.

## Try PoCo in 5 minutes
Needs Python 3.10–3.13, `make` and a clone of this repository. The demo uses the synthetic slide in the repository; no laboratory data.
```bash
git clone https://github.com/oriamos/poco.git && cd poco
make app-install   # creates .venv and installs the Python dependencies (first run only)
make demo          # copies the synthetic slide to ./demo-data/input and starts the app on ./demo-data/app
```
Open **http://127.0.0.1:8000** and follow [TRY_DEMO.md](TRY_DEMO.md): open `demo-data/input/test_img.tif`, map the channels (red = channel 0, green = channel 1), generate the grid, detect, review, save. Install, start, open and detect take a few minutes; review takes as long as you spend. Expected output files and the reset command are in TRY_DEMO.md. `make demo-reset` deletes the demo folder only.
**Windows without `make`:** use the installer below, or run this in PowerShell from the cloned folder, then open the slide from `demo-data\input`:
```powershell
python -m venv .venv; .venv\Scripts\pip install -r requirements-app.txt
New-Item -ItemType Directory -Force demo-data\input | Out-Null; Copy-Item resources\dataset_files\test\test_img.tif demo-data\input\
$env:PYTHONPATH='src'; .venv\Scripts\python -m polony_app --data-dir demo-data\app --port 8000
```

## Install (one command, no administrator rights)
Release **v0.3.4** (research software, see the status below). The installers download this tagged release, not the moving `main` branch.
**Windows** (PowerShell):
```powershell
irm https://raw.githubusercontent.com/oriamos/poco/v0.3.4/install/install.ps1 | iex
```
**macOS / Linux** (Terminal):
```bash
curl -fsSL https://raw.githubusercontent.com/oriamos/poco/v0.3.4/install/install.sh | bash
```
It installs into your user folder (about 650 MB; downloads Python 3.12 only when no Python 3.10–3.13 is present) and adds a **PoCo / Polony Review** desktop icon. Uninstalling keeps your data folder.
**Update** (no full re-download; libraries, AI detector, settings and data are kept), from version 0.3.1 on:
```bash
~/PolonyReview/bin/polony-review update --check   # is there a newer release?
~/PolonyReview/bin/polony-review update
```
On Windows: `& "$env:LOCALAPPDATA\PolonyReview\venv\Scripts\python.exe" -m polony_app.launcher update`. An older installation updates once by running the install command again. Details: [docs/app/INSTALL.md](docs/app/INSTALL.md).
**Safer alternative** (no script piped into a shell): download the script and the release's `SHA256SUMS.txt`, verify the checksum, read the script, run it.
```bash
base=https://github.com/oriamos/poco/releases/download/v0.3.4
curl -fsSLO $base/install.sh && curl -fsSLO $base/SHA256SUMS.txt
grep ' install.sh$' SHA256SUMS.txt | sha256sum -c -     # macOS: ... | shasum -a 256 -c -    (must print: install.sh: OK)
less install.sh
bash install.sh
```
On Windows, download `install.ps1` and `SHA256SUMS.txt` from the same release page, compare `(Get-FileHash install.ps1 -Algorithm SHA256).Hash` with the `install.ps1` line of `SHA256SUMS.txt`, read the script, then run `powershell -NoProfile -ExecutionPolicy Bypass -File install.ps1`.

* **AI detector (Spotiflow + PyTorch, about 0.8–2.5 GB extra, plus the 47 MB fine-tuned model):** add `--with-ai` (`-WithAi` on Windows). The installer also downloads the fine-tuned model, checks its SHA-256 and makes it the default. Apple Silicon uses the GPU when available. Intel Macs: older PyTorch 2.2.2, CPU only.
* Install, update, uninstall, troubleshooting: [docs/app/INSTALL.md](docs/app/INSTALL.md). Development branch (unstable, testing only): set `POLONY_REF=main` before running the installer.

## What the scientific results do and do not show
* **Big-FISH** is the classical detector: deterministic, with background subtraction and a threshold.
* **Spotiflow** is the optional AI detector. A fresh AI install uses the **shipped fine-tuned model** `ft-7e4c89cb-8edc09e3` by default (downscale 4, normaliser `valid_unsaturated`, threshold 0.3, applied automatically). The pretrained `general` model stays in the model picker; models you train and promote replace the default. The run record names the model by registry id and weights checksum.
* **Agreement between two detectors is not ground truth.** Where they agree the count is more likely right; where they differ, a person decides.
* **Human review remains required.** Nothing is final until a person finalizes the analysis. **Training never runs automatically.** It only happens when you run the training command yourself.
* **The fine-tuned weights are a [release asset](https://github.com/oriamos/poco/releases/tag/model-ft-7e4c89cb-8edc09e3)**, not part of the git repository; the installer downloads and verifies them. The laboratory approved distribution. The licence of the *upstream pretrained* Spotiflow weights is still unconfirmed ([MODEL_CARD.md](MODEL_CARD.md)). What is and is not connected: [docs/STATUS_AND_RESULTS.md](docs/STATUS_AND_RESULTS.md).

Results so far ([docs/STATUS_AND_RESULTS.md](docs/STATUS_AND_RESULTS.md)): an **exploratory evaluation on eight real slides with one annotator** (varies a lot from slide to slide; not validation), and a **fine-tuning run on saved historical data** (the shipped model) (test split: 1,980 crops from 97 groups). Agreement with the saved researcher marks, at a 10-pixel tolerance, each model at its own threshold:

| | Pretrained | Shipped fine-tuned model |
|---|---:|---:|
| Precision | 64.89% | 75.14% |
| Recall | 73.95% | 91.36% |
| F1 | 69.13% | 82.46% |
| Count error per field (MAE) | 3.282 | 2.014 |
| Count bias per field | +1.243 | +1.921 |

These numbers measure **agreement with saved marks, not accuracy** on new images. The model also **over-counts more** than the pretrained one (count bias +1.921 against +1.243 per field), so review every field. The original test images are not distributed, so the evaluation cannot be re-run.

## Status and limitations
* **Status:** research software, release 0.3.4. Run end to end on real two-channel slides against the researcher's marks; accuracy is partial and the defaults are not final.
* **Limitations:** pixel size is not applied to distances (everything is in image pixels unless you set it); the shipped model's evaluation is agreement with saved marks only and its base-weights licence is unconfirmed ([MODEL_CARD.md](MODEL_CARD.md)); Intel Macs run the AI detector on CPU with PyTorch 2.2.2 (untested on hardware); Apple Silicon Spotiflow falls back to CPU for unsupported operations.
* **Test results** are in the CI badges above and the [CI workflow runs](https://github.com/oriamos/poco/actions). This README does not copy test counts, which go stale.

## Documentation
| I want to... | Read |
|---|---|
| Try the demo | [TRY_DEMO.md](TRY_DEMO.md) |
| Install, update, uninstall, fix an install | [docs/app/INSTALL.md](docs/app/INSTALL.md) |
| Use the app, step by step | [docs/app/USER_GUIDE.md](docs/app/USER_GUIDE.md) |
| Understand a parameter or a review flag | [docs/app/PARAMETERS.md](docs/app/PARAMETERS.md) |
| Know what is validated and what is not | [docs/STATUS_AND_RESULTS.md](docs/STATUS_AND_RESULTS.md) |
| Train or fine-tune a model | [docs/app/TRAINING_GUIDE.md](docs/app/TRAINING_GUIDE.md), then [docs/app/FINE_TUNING.md](docs/app/FINE_TUNING.md) and [docs/app/LEGACY_FINETUNING.md](docs/app/LEGACY_FINETUNING.md) |
| Evaluate a model | [docs/app/EVALUATION.md](docs/app/EVALUATION.md), results so far: [docs/app/ALL_SLIDES_EVAL.md](docs/app/ALL_SLIDES_EVAL.md); model information: [MODEL_CARD.md](MODEL_CARD.md), [artifacts/README.md](artifacts/README.md) |
| Call the API | [docs/app/EXPERIMENTS_API.md](docs/app/EXPERIMENTS_API.md), and the live docs at `/docs` while the app runs |
| See what is planned | [docs/app/ROADMAP.md](docs/app/ROADMAP.md), [docs/app/SCIENTIFIC_OPEN_QUESTIONS.md](docs/app/SCIENTIFIC_OPEN_QUESTIONS.md) |
| Reproducibility (what can and cannot be rerun) | [docs/REPRODUCIBILITY.md](docs/REPRODUCIBILITY.md) |
| Contribute | [CONTRIBUTING.md](CONTRIBUTING.md), [SECURITY.md](SECURITY.md), [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) |
| Release notes, everything | [CHANGELOG.md](CHANGELOG.md), [docs/app/README.md](docs/app/README.md) |

## Developer setup
```bash
make app        # venv + dependencies + frontend build (if npm) + server on http://127.0.0.1:8000
make app-test   # backend tests (pytest, tests/app)
make web        # rebuild the committed UI in src/polony_app/webdist after a frontend change
cd frontend && npm ci && npx tsc --noEmit && npx vitest run && npm run e2e
```
Backend: `src/polony_app` (FastAPI, SQLite, optional shared Postgres). Frontend: `frontend/` (React, TypeScript). Checklist and rules for scientific claims and data: [CONTRIBUTING.md](CONTRIBUTING.md).

## Authors, acknowledgements and citation
* **Software design and implementation:** Ori Amos. See [AUTHORS.md](AUTHORS.md).
* **Upstream attribution:** file conventions for the historical ImageJ TIFFs were learned from [kirill-push/polony-counting](https://github.com/kirill-push/polony-counting) (MIT); no code was copied. See [NOTICE](NOTICE).
* **Background:** polony is a solid-phase single-molecule PCR method (Mitra & Church, 1999), adapted at the Lindell lab, Technion, to quantify marine viruses of a given clade in field samples.
* **Citation:** [CITATION.cff](CITATION.cff). A preprint or paper citation will be added when one exists.
* **Feedback:** Open an issue (use the templates) for bugs and suggestions. Do not attach laboratory images or other research data to public issues. Security problems: [SECURITY.md](SECURITY.md).

## License
MIT, see [LICENSE](LICENSE). Big-FISH and Spotiflow are separate projects with their own licences; see [NOTICE](NOTICE).
