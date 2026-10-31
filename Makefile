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

extract: ## extract obligations from pending clauses (respects the daily token budget)
	$(PY) -m app.extract.run --limit 2000

eval-obligations: ## measure obligation extraction on the gold set (calls the model)
	$(PY) -m app.extract.eval

audit: ## check pinned dependencies for known vulnerabilities
	$(PY) -m pip_audit -r requirements.txt

db-init: ## create the Postgres tables from sql/001_init.sql
	$(PY) -m app.db

ingest: ## load RBI circulars into Postgres
	$(PY) -m app.ingest.run

daily: ## fetch new RBI and SEBI documents once
	$(PY) -m app.ingest.daily

schedule: ## install a 06:00 daily launchd job (macOS)
	mkdir -p $(HOME)/Library/LaunchAgents data/logs
	sed -e 's|__PROJECT_DIR__|$(CURDIR)|g' -e 's|__PYTHON__|$(CURDIR)/.venv/bin/python|g' scripts/launchd/com.regintel.daily.plist.template > $(HOME)/Library/LaunchAgents/com.regintel.daily.plist
	-launchctl unload $(HOME)/Library/LaunchAgents/com.regintel.daily.plist
	launchctl load $(HOME)/Library/LaunchAgents/com.regintel.daily.plist
	@echo "installed: daily at 06:00, logs in data/logs/"

unschedule: ## remove the daily launchd job
	-launchctl unload $(HOME)/Library/LaunchAgents/com.regintel.daily.plist
	rm -f $(HOME)/Library/LaunchAgents/com.regintel.daily.plist
	@echo "removed daily job"

clean: ## remove caches and the virtualenv
	rm -rf .venv .pytest_cache
	find . -name __pycache__ -type d -prune -exec rm -rf {} +

.PHONY: help setup test eval eval-obligations extract audit db-init ingest daily schedule unschedule clean
