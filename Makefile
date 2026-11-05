PY ?= python3
WORKERS ?= 2
export PYTHONPATH := $(CURDIR)

.DEFAULT_GOAL := help

.PHONY: help install browsers app test test-api test-ui test-smoke test-parallel lint docker-build docker-test clean

help:
	@echo "Harbor Market QA"
	@echo "  make install          install Python dependencies"
	@echo "  make browsers         install Chromium for Playwright"
	@echo "  make app              run the demo shop on http://127.0.0.1:8000"
	@echo "  make test             API + UI, parallel, HTML report"
	@echo "  make test-api         API suite only"
	@echo "  make test-ui          UI suite only"
	@echo "  make test-smoke       smoke marker only"
	@echo "  make test-parallel    same suite with all CPU workers"
	@echo "  make lint             ruff"
	@echo "  make docker-test      build the image and run the suite"
	@echo "  make clean            delete reports and caches"

install:
	$(PY) -m pip install -r requirements.txt

browsers:
	$(PY) -m playwright install --with-deps chromium

app:
	$(PY) -m uvicorn demo_app.main:app --host 127.0.0.1 --port 8000 --reload

test:
	mkdir -p reports
	$(PY) -m pytest -n $(WORKERS) --html=reports/report.html --self-contained-html

test-api:
	mkdir -p reports
	$(PY) -m pytest -m api -n $(WORKERS) --html=reports/api-report.html --self-contained-html

test-ui:
	mkdir -p reports
	$(PY) -m pytest -m ui -n $(WORKERS) --html=reports/ui-report.html --self-contained-html

test-smoke:
	mkdir -p reports
	$(PY) -m pytest -m smoke -n $(WORKERS) --html=reports/smoke-report.html --self-contained-html

test-parallel:
	mkdir -p reports
	$(PY) -m pytest -n auto --html=reports/report.html --self-contained-html

lint:
	$(PY) -m ruff check .

docker-build:
	docker build -t harbor-qa .

docker-test: docker-build
	docker run --rm -v "$(CURDIR)/reports:/work/reports" harbor-qa

clean:
	rm -rf reports test-results .pytest_cache .ruff_cache
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
