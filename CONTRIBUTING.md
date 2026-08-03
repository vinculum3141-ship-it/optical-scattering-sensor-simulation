# Contributing

## Setup

```bash
git clone <repo>
cd optical-scattering-sensor-simulation
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Running tests

```bash
# Pytest unit tests
python -m pytest -v

# Robot Framework acceptance tests
python -m robot tests/
```

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
