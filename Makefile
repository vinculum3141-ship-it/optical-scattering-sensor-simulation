.PHONY: install dev demo test test-v acceptance docs docs-build clean

install:           ## Install the package in editable mode
	python -m pip install -e .

dev:               ## Install with development + analysis + visualisation extras
	python -m pip install -e ".[dev,analysis,visualisation]"

demo:              ## Run the non-interactive pipeline tour
	python playground.py --demo

test:              ## Run the unit/integration test suite
	python -m pytest -q

test-v:            ## Run the unit/integration test suite verbosely
	python -m pytest -v

acceptance:        ## Run the Robot Framework acceptance tests
	python -m robot tests/

docs:              ## Serve the documentation site locally (http://127.0.0.1:8000)
	python -m mkdocs serve

docs-build:        ## Build the documentation site (strict, fails on broken links)
	python -m mkdocs build --strict

clean:             ## Remove build artifacts
	rm -rf site .pytest_cache build dist
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
