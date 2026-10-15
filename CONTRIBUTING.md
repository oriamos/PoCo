# Contributing

PoCo / Polony Review counts polonies for research. Keep the researcher in control of every count; back every scientific claim with evidence. Read the privacy rules and claims policy first.

## Set up and test

Python 3.10 to 3.13 (CI: full suite on 3.12, smoke subset on 3.10, 3.11, 3.13), Node.js 20, `make`.

```bash
make app            # .venv, dependencies, frontend build (if npm is present), server on http://127.0.0.1:8000
make app-install    # only create .venv and install requirements-app.txt
make app-run        # only start the server (PORT=... changes the port)
make app-install APP_PY=python   # use your own interpreter instead of .venv
make app-test       # backend: PYTHONPATH=src python -m pytest tests/app -q (torch/Spotiflow/GPU tests skip without them)
```

CI deselects four heavy tests; to match it:

```bash
PYTHONPATH=src python -m pytest tests/app -q \
  --deselect tests/app/test_ml_devices_scale.py \
  --deselect tests/app/test_preflight_rehearsal.py \
  --deselect tests/app/test_engines_pipeline.py::test_hybrid_end_to_end \
  --deselect tests/app/test_ml_fault_injection.py::test_import_of_a_few_hundred_files_has_a_flat_memory_profile
```

Frontend, from `frontend/`, in this order (as CI):

```bash
npm ci
npx tsc --noEmit                 # type check
npx vitest run                   # unit tests
npm run build                    # production build
CHROMIUM_PATH=/path/to/chromium npm run e2e   # end-to-end in real Chromium against the mock API
npx playwright-core install chromium          # if you need a browser for Playwright
```

`CHROMIUM_PATH` must point to a Chromium binary; if unset, the script checks its default locations.

## Rebuild the committed UI

`src/polony_app/webdist` is committed and served by the installers. After any change in `frontend/`, run `make web` and commit the rebuilt `webdist` in the same pull request.

## Documentation rules

- Short, plain English; no marketing language. No test counts (describe the command). No internal process notes, session logs or agent instructions.
- Put the scientific limits of a result next to the result.
- Check links and anchors of every changed Markdown file (CI runs it): `python scripts/check_markdown_links.py .`

## Scientific claims policy

- Keep **exploratory evaluation** (what happened on the data used) apart from **validation** (pre-stated protocol, locked test set, documented sample sizes).
- Agreement with a researcher's marks is agreement with those marks, not general accuracy. A missed mark counts as a false positive.
- No accuracy claim without a test documented in the repository. State thresholds, tolerance (for example 10 native pixels), sample sizes (slides, fields, groups) and configuration.
- Do not change default parameters or the default model unless the evidence is in the pull request and in the docs.
- Results so far: the saved registry (not published; see [artifacts/README.md](artifacts/README.md)) and [docs/app/TRAINING_GUIDE.md](docs/app/TRAINING_GUIDE.md).

## Privacy and data rules

Never commit: TIFF images, CSV or Excel results or provenance files from the laboratory; patient-like or identifying data; credentials, passwords, tokens or database URLs (`POLONY_DATABASE_URL` and `config.json` contain them); local paths such as `/home/...` or `C:\Users\...`.

- Use synthetic data or `resources/dataset_files/test` (its `test_img.tif` is synthetic).
- Committed a private file by mistake: tell the maintainer at once. Removing it from the latest commit is not enough; git keeps the history.

## Pull requests

- One small, focused change; add or update tests for every behaviour change; update the docs of the changed behaviour.
- CI green before review. Never weaken, skip or delete a test to pass CI; if a test is wrong, explain why in the pull request.
- Fill in the pull request template, including the privacy check.

## Releasing (maintainers)

1. Set the new version in `pyproject.toml`, `src/polony_app/__init__.py` and `frontend/package.json`. Add a `## X.Y.Z` section to `CHANGELOG.md`. Update `constraints/release-X.Y.Z.txt` ([docs/REPRODUCIBILITY.md](docs/REPRODUCIBILITY.md)), the installer defaults (`install/install.sh`, `install/install.ps1`) and the README commands.
2. Merge to `main`; wait for CI and `install-test` to pass.
3. Actions, workflow `release`, "Run workflow" on `main` with the version. It checks the versions, refuses a commit whose checks are not green, creates the annotated tag, and publishes the release with the installers and `SHA256SUMS.txt`.
4. Check the release: download the assets, verify `SHA256SUMS.txt`, run the README install command in a clean environment.
