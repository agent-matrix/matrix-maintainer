PYTHON ?= python3.11
UV ?= uv

.PHONY: install dev test lint format start build-site run-daily clean

install:
	$(UV) sync

dev: install

test:
	$(UV) run pytest -q

lint:
	$(UV) run python -m compileall matrix_codex
	$(UV) run pytest -q tests/unit

format:
	@echo "No formatter configured by default; add ruff/black if desired."

start:
	$(UV) run matrix-codex --help

build-site:
	$(UV) run matrix-codex publish-site

run-daily:
	$(UV) run matrix-codex run-daily

clean:
	rm -rf .pytest_cache htmlcov dist build tmp
