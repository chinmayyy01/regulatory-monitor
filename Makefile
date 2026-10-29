PYTHON ?= python3
PY := .venv/bin/python
PIP := .venv/bin/pip

.DEFAULT_GOAL := help

help:
	@grep -E '^[a-zA-Z_-]+:.*## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "}; {printf "  %-10s %s\n", $$1, $$2}'

setup: ## create .venv and install pinned dependencies
	$(PYTHON) -m venv .venv
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt -r requirements-dev.txt

test: ## run the offline test suite (no network, no API calls)
	$(PY) -m pytest

eval: ## run the evaluation harness (intentionally fails until W2)
	$(PY) scripts/eval.py

audit: ## check pinned dependencies for known vulnerabilities
	$(PY) -m pip_audit -r requirements.txt

db-init: ## create the Postgres tables from sql/001_init.sql
	$(PY) -m app.db

ingest: ## load RBI circulars into Postgres
	$(PY) -m app.ingest.run

clean: ## remove caches and the virtualenv
	rm -rf .venv .pytest_cache
	find . -name __pycache__ -type d -prune -exec rm -rf {} +

.PHONY: help setup test eval audit db-init ingest clean
