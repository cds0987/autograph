# Publish To PyPI

## Goal

After this project is pushed to GitHub and linked to PyPI, users should be able to install it with:

```bash
pip install autograph-llmneo4j
```

Python imports stay the same:

```python
from autograph import GraphBuilder
```

## Local Release Steps

Build and validate the package locally:

```powershell
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install build twine
.venv\Scripts\python.exe -m build
.venv\Scripts\python.exe -m twine check dist/*
```

Optionally test install from the built wheel:

```powershell
.venv\Scripts\python.exe -m pip install --force-reinstall --no-deps dist\autograph_llmneo4j-0.1.0-py3-none-any.whl
```

## GitHub Actions

This repository includes:

- `.github/workflows/ci.yml`
- `.github/workflows/publish-pypi.yml`

`ci.yml` runs package installation and a lightweight test subset on pushes and pull requests.

`publish-pypi.yml` builds distributions on release publication and publishes them to PyPI.

## PyPI Setup

You have two options:

### Recommended: Trusted Publishing

In PyPI:

1. Create the project or reserve the name `autograph-llmneo4j`
2. Go to the project publishing settings
3. Add a trusted publisher for GitHub repository `cds0987/autograph`
4. Point it to the `publish-pypi.yml` workflow

With trusted publishing, GitHub Actions can publish without storing a long-lived API token.

### Alternative: API Token

If you prefer a token:

1. Create a PyPI API token
2. Store it as `PYPI_API_TOKEN` in GitHub repository secrets
3. Update the publish workflow to use that token instead of trusted publishing

## Release Flow

1. Commit and push changes to GitHub
2. Make sure CI passes
3. Create a Git tag such as `v0.1.0`
4. Publish a GitHub release for that tag
5. GitHub Actions builds and publishes the package to PyPI

## Notes

- GitHub repository URL: `https://github.com/cds0987/autograph`
- PyPI distribution name: `autograph-llmneo4j`
- Python import package: `autograph`
- Bump the version in `pyproject.toml` before each release
- If you add optional providers later, consider using optional dependency groups
