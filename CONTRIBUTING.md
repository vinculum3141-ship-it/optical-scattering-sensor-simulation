# Contributing

## Setup

```bash
git clone <repo>
cd optical-scattering-sensor-simulation
python -m venv .venv
source .venv/bin/activate
make dev        # or: pip install -e ".[dev,analysis,visualisation]"
```

## Running tests

```bash
# Pytest unit tests
make test        # or: python -m pytest -q

# Robot Framework acceptance tests
make acceptance  # or: python -m robot tests/
```

## Building the documentation

The docs are a [mkdocs](https://www.mkdocs.org/) site under `docs/` with
a Material theme. The `.[docs]` extra installs everything needed.

```bash
# Local preview at http://127.0.0.1:8000
make docs        # or: python -m mkdocs serve

# Strict build — fails on broken links or nav errors (what CI runs)
make docs-build  # or: python -m mkdocs build --strict
```

Keep every doc link and the `mkdocs.yml` nav in sync; the strict build
enforces this in CI.

## Code style

- Follow existing patterns (dataclasses for data containers, abstract base
  classes for pluggable models, NumPy for array operations).
- All physical quantities use SI units.
- Keep the dependency footprint minimal — prefer pure NumPy over SciPy
  where possible.

## Pull request workflow

1. Open an issue for discussion before starting significant work.
2. Implement changes with tests covering new functionality.
3. Run the full test suite (`python -m pytest -q`) and confirm all tests pass.
4. Update docs if the public API changes.
5. Submit a PR with a clear description of the change.
