PYTHON ?= python
.PHONY: api web test build lint
api:
	$(PYTHON) -m uvicorn app.main:app --host 127.0.0.1 --port 8100
web:
	npm --prefix apps/web run dev
test:
	$(PYTHON) -m pytest -q
build:
	npm run build
lint:
	$(PYTHON) -m ruff check apps/api tests
