# Contributing

Thank you for helping with PoCo / Polony Review. This project counts polonies for research. Changes must keep the
researcher in control of every count, and every scientific claim must be backed by evidence.

Please read the privacy rules and the scientific claims policy before you start.

## Set up the environment

Requirements: Python 3.10 to 3.13 (CI uses 3.12), Node.js 20 (CI uses 20), and `make`.

```bash
make app            # virtualenv (.venv), dependencies, frontend build (if npm is present), server on http://127.0.0.1:8000
make app-install    # only create .venv and install requirements-app.txt
make app-run        # only start the server (PORT=... to change the port)
make web            # rebuild the committed UI in src/polony_app/webdist after a frontend change

cd frontend && npm ci   # frontend dependencies from package-lock.json
```

Use your own interpreter with `make app-install APP_PY=python` if you do not want `.venv`.

## Run the tests

### Backend

```bash
make app-test
```

This runs `PYTHONPATH=src python -m pytest tests/app -q`. Some tests need torch, Spotiflow or a GPU and are skipped
on machines without them.

CI runs the same suite with four heavy tests deselected. Run this command to match CI:

```bash
PYTHONPATH=src python -m pytest tests/app -q \
  --deselect tests/app/test_ml_devices_scale.py \
  --deselect tests/app/test_preflight_rehearsal.py \
  --deselect tests/app/test_engines_pipeline.py::test_hybrid_end_to_end \
  --deselect tests/app/test_ml_fault_injection.py::test_import_of_a_few_hundred_files_has_a_flat_memory_profile
```

### Frontend

Run these from the `frontend/` folder, in this order (this is what CI does):

```bash
npm ci
npx tsc --noEmit                 # type check
npx vitest run                   # unit tests
npm run build                    # production build
CHROMIUM_PATH=/path/to/chromium npm run e2e   # end-to-end checks in real Chromium against the mock API
```

`CHROMIUM_PATH` must point to a Chromium binary. If it is not set, the script looks in its default locations.
To install a browser for Playwright, run `npx playwright-core install chromium`.

## Rebuild the committed UI

The installers serve the web interface from `src/polony_app/webdist`, which is committed to git. After any change in
`frontend/`, run `make web` and commit the rebuilt `src/polony_app/webdist` in the same pull request as the frontend
change.

## Documentation rules

- Keep new text short and in plain English. Do not use marketing language.
- Check that the relative links and anchors in every changed Markdown file resolve: `python scripts/check_markdown_links.py .`
  (CI runs the same check).
- Do not write test counts into documentation. They go out of date. Describe the command instead.
- Do not add internal process notes, session logs, or agent instructions to public files.
- Put the scientific limits of a result next to the result.

## Scientific claims policy

- Separate **exploratory evaluation** from **validation**. An exploratory run shows what happened on the data used. A
  validation uses a pre-stated protocol, a locked test set, and documented sample sizes.
- Agreement with a researcher's marks is agreement with those marks. It is not general accuracy. A missed mark counts as
  a false positive.
- Never claim accuracy unless a test that is documented in the repository supports it.
- Always state the thresholds, the tolerance (for example 10 native pixels), the sample sizes (slides, fields, groups),
  and the configuration used.
- Do not change the default parameters or the default model in a pull request unless the evidence is in the pull
  request and in the docs.
- See the saved registry (not published; see [artifacts/README.md](artifacts/README.md)) and [docs/app/TRAINING_GUIDE.md](docs/app/TRAINING_GUIDE.md)
  for the results recorded so far.

## Privacy and data rules

Never commit any of the following:

- TIFF images, CSV or Excel results, or provenance files from the laboratory.
- Patient-like or identifying data of any kind.
- Credentials, passwords, tokens, or database URLs (`POLONY_DATABASE_URL` and `config.json` contain them).
- Local paths from your computer, such as `/home/...` or `C:\Users\...`.

For tests and examples, use synthetic data or the files in `resources/dataset_files/test`. The example
`test_img.tif` there is synthetic.

If you commit a private file by mistake, tell the maintainer at once. Removing it from the latest commit is not enough,
because git keeps the history.

## Pull requests

- Keep each pull request small and focused on one change.
- Add or update tests for every behaviour change.
- Make sure CI is green before you ask for review.
- Update the documentation that describes the changed behaviour.
- Do not weaken, skip or delete a test to make CI pass. If a test is wrong, explain why in the pull request.
- Fill in the pull request template, including the privacy check.
