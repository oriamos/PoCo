# Security policy

## Supported versions

| Version | Supported |
|---|---|
| 0.1.x (current research release, `version` in `pyproject.toml`) | Yes |
| Older untagged commits on `main` | No |

## Reporting a vulnerability

- Report privately; no public issue or pull request. Use GitHub private vulnerability reporting: <https://github.com/oriamos/poco/security/advisories/new>
- TODO (Ori): enable private vulnerability reporting (Settings, Code security, Private vulnerability reporting). The link does not work until it is enabled.
- Include the app version, operating system, steps to reproduce and the effect. No real research data or credentials: describe the data type instead.

## What the app protects

The app runs on your computer and uploads nothing itself. Its data is sensitive:

- **Imported images, exports, provenance files** (`experiment_counts.csv`, Excel workbooks, provenance JSON) can contain research data. Do not share them publicly or attach them to public issues.
- **Shared-database URL** (`POLONY_DATABASE_URL` or `config.json`) contains a password. Keep `config.json` readable only by you (mode 600 on macOS and Linux). Never paste the URL into an issue, chat or screenshot. See [docs/app/SHARED_DATABASE.md](docs/app/SHARED_DATABASE.md).

## Local API and network

- The local API has **no login and no authentication**: anyone who can use your computer account can open the app and read its data.
- The server listens on `127.0.0.1` by default (`python -m polony_app` and the desktop launcher). `--host` can change it; do not set a network address.
- Do not expose the port (port forwarding, tunnel, reverse proxy). Localhost binding is not a security boundary against other users of the same computer.

## Installer

- `install/install.sh` and `install/install.ps1` download over HTTPS from `github.com`, `pypi.org`, `download.pytorch.org` (AI detector only) and `astral.sh` (only if no suitable Python is installed).
- They run without administrator rights, install into your user folder, and do not use `sudo`.
- The AI installer downloads the fine-tuned model from the `model-ft-7e4c89cb-8edc09e3` release and accepts it only if size and SHA-256 equal the values pinned in `src/polony_app/ml/bundled_model.py`; a different file is deleted, never loaded.
- They install the tagged release (`v0.3.5` for this version), not `main`; `POLONY_REF=main` installs the unstable development branch.
- Each GitHub Release attaches the installer scripts and `SHA256SUMS.txt`. The README shows how to download the script, verify its SHA-256, read it, then run it. `curl ... | bash` runs code you have not read; use the verified path for a version you have not reviewed.
- Not verified: the hash of the application archive and of the Python packages (package downloads use HTTPS and PyPI's integrity checks). Planned: verify the application archive against the release checksum.

## Dependencies and updates

- `requirements-app.txt` has minimum versions only (`>=`). `constraints/release-0.3.0.txt` records the exact tested versions ([docs/REPRODUCIBILITY.md](docs/REPRODUCIBILITY.md)); the installers do not use it.
- Optional AI packages are pinned: `spotiflow==0.6.5`, `torch==2.14.1`, `torchvision==0.29.1`. The frontend uses `frontend/package-lock.json` with exact versions.
- Dependabot (`.github/dependabot.yml`): weekly for Python, npm and GitHub Actions. Minor and patch updates arrive as pull requests and must pass CI. Major-version jumps of Python and npm packages are ignored (they need a deliberate migration); security updates are not affected.
