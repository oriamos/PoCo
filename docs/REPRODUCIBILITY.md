# Reproducibility

What you can rerun from this repository, what you cannot, and how to reproduce the pipeline on your own data. Bit-for-bit reproducibility is **not** claimed: floating-point results can differ between CPUs, BLAS builds, library versions and thread counts.

## What can be reproduced from the public files

| Item | How |
|---|---|
| Application behaviour on the synthetic demo slide | [TRY_DEMO.md](../TRY_DEMO.md); `tests/app/test_demo_smoke.py`. The slide is generated (seeded) by `resources/dataset_files/test/make_test_img.py`; its truth is in `test_img.truth.json`. |
| Backend and frontend test suites | `make app-test`; `cd frontend && npx vitest run && npm run e2e`. CI runs them on every push. |
| Supported Python versions | CI runs the full backend suite on 3.12 and a smoke subset on 3.10, 3.11 and 3.13. |
| Installers | the `install-test` workflow runs them on Linux, macOS and Windows. The optional AI install is tested only in manual runs. |
| Recorded model checksums | [MODEL_CARD.md](../MODEL_CARD.md) (they identify files held by the laboratory) |

## What cannot be reproduced from the public files

| Item | Why |
|---|---|
| Eight-slide exploratory evaluation ([ALL_SLIDES_EVAL.md](app/ALL_SLIDES_EVAL.md)) | The slides and the researcher's marks are unpublished laboratory data. |
| Saved-data fine-tuning run and its metrics ([STATUS_AND_RESULTS.md](STATUS_AND_RESULTS.md), section B) | The historical TIFFs, the dataset snapshot manifest and the test crops are not in the repository; the checkpoint is a verified release asset ([MODEL_CARD.md](../MODEL_CARD.md)), so inference with it can be rerun, but the evaluation cannot. Only the locked test-set record (`artifacts/test-set/test_lock.json`) and the configuration are public. |
| Whether identity mapping and annotation completeness were right | Not verifiable from the saved artifacts alone. |

## Dependencies

* `requirements-app.txt`: direct runtime and test requirements with minimum versions; the installers use it.
* `constraints/release-0.3.0.txt`: exact versions installed and tested for the 0.3.0 release. CI installs with it on Python 3.12 and runs the smoke tests. It excludes the optional AI packages (Spotiflow, PyTorch); the AI installer pins its own in `install/extra-ai-requirements.txt`.

Install with the constraints:

```bash
pip install -r requirements-app.txt -c constraints/release-0.3.0.txt
```

Regenerate the constraints for a new release in a clean virtual environment, then add the three header comment lines:

```bash
python -m venv /tmp/venv && /tmp/venv/bin/pip install -r requirements-app.txt
/tmp/venv/bin/pip freeze > constraints/release-X.Y.Z.txt
```

## Reproducing the pipeline on your own data

1. Install a tagged release ([README](../README.md)). Keep the version, the `constraints` file and the provenance JSON of each analysis (parameters, model, seeds, hashes, package versions).
2. Run detection with fixed parameters and note the engine versions in the provenance. Grid randomisation records its seed.
3. For training and evaluation, follow [app/TRAINING_GUIDE.md](app/TRAINING_GUIDE.md). A dataset snapshot freezes crops, labels, settings and split; a test lock freezes the test material. Keep both with the model and report the tolerance and thresholds used.
4. Share metrics only as agreement with your own saved marks, with sample sizes and thresholds ([CONTRIBUTING.md](../CONTRIBUTING.md)).
