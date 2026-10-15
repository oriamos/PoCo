# Security policy

## Supported versions

| Version | Supported |
|---|---|
| 0.1.x (current research release, `version` in `pyproject.toml`) | Yes |
| Older untagged commits on `main` | No |

## Reporting a vulnerability

Please report security problems privately. Do not open a public issue or a public pull request.

Use GitHub private vulnerability reporting on this repository:
<https://github.com/oriamos/poco/security/advisories/new>

TODO (Ori): enable private vulnerability reporting in the repository settings (Settings, Code security, Private
vulnerability reporting). The link above does not work until it is enabled.

Please include the app version, your operating system, the steps to reproduce the problem, and its effect. Do not
include real research data or credentials in the report. Describe the data type instead.

## What the app protects, and what it does not

PoCo / Polony Review runs on your own computer. Nothing is uploaded by the app itself. But the data it handles is
sensitive, and some of it contains secrets:

- **Imported images, exports, and provenance files** (`experiment_counts.csv`, Excel workbooks, the provenance JSON)
  can contain research data. Do not share them publicly, and do not attach them to public issues.
- **The shared-database URL** (`POLONY_DATABASE_URL` or `config.json`) contains a password. Keep `config.json` readable
  only by your own account (mode 600 on macOS and Linux). Never paste the URL into an issue, a chat, or a screenshot.
  See [docs/app/SHARED_DATABASE.md](docs/app/SHARED_DATABASE.md).

## Local API and network exposure

- The local API has **no login and no authentication**. Anyone who can use your computer account can open the app
  and read its data.
- The server listens on `127.0.0.1` by default. The `python -m polony_app` command and the desktop launcher both use
  this address. The `--host` option of `python -m polony_app` can change the address. Do not change it to a network
  address.
- Do not expose the port with port forwarding, a tunnel, or a reverse proxy.
- Localhost binding is not a security boundary against other users of the same computer.

## Installer

- The installers (`install/install.sh`, `install/install.ps1`) download code and tools over HTTPS from `github.com`,
  `pypi.org`, `download.pytorch.org` (AI detector only), and `astral.sh` (only if no suitable Python is installed).
- The installers run without administrator rights. They install into your user folder and do not use `sudo`.
- By default the installers install the tagged release (`v0.1.0` for this version), not the moving `main` branch. `POLONY_REF=main`
  installs the unstable development branch.
- Each GitHub Release attaches the installer scripts and a `SHA256SUMS.txt`. The README shows how to download the script, verify its
  SHA-256 value, read it, and then run it. Running `curl ... | bash` runs code from the internet without a chance to read it
  first; use the verified path for a version you have not reviewed.
- The installers do **not** verify the hash of the application archive or of the Python packages they download. Package downloads
  use HTTPS and PyPI's own integrity checks. Planned: verifying the application archive against the release's checksum.

## Dependencies and updates

- The Python dependencies in `requirements-app.txt` have minimum versions only (`>=`). `constraints/release-0.1.0.txt` records the exact versions tested for the release (see
  [docs/REPRODUCIBILITY.md](docs/REPRODUCIBILITY.md)); it is not used by the installers. The optional AI packages are pinned exactly (`spotiflow==0.6.5`, `torch==2.14.1`, `torchvision==0.29.1`).
- The frontend uses `frontend/package-lock.json` with exact versions.
- Dependabot is configured (`.github/dependabot.yml`) for the Python, npm and GitHub Actions dependencies, weekly. Updates arrive as pull requests and
  must pass CI before they are merged.
