PYTHON ?= python3
VENV_DIR = .venv
PYTHON_BIN = $(VENV_DIR)/bin/python
PIP = $(VENV_DIR)/bin/pip
PYTEST = $(VENV_DIR)/bin/pytest
UVICORN = $(VENV_DIR)/bin/uvicorn

.PHONY: help venv install test run clean

help:
	@echo "Available targets:"
	@echo "  make install  - Create virtualenv (if missing) and install dependencies"
	@echo "  make test     - Run pytest inside the virtualenv"
	@echo "  make run      - Start uvicorn with auto-reload"
	@echo "  make clean    - Remove the virtualenv"

venv:
	@if [ ! -d "$(VENV_DIR)" ]; then \
		echo "Creating virtual environment at $(VENV_DIR)"; \
		$(PYTHON) -m venv $(VENV_DIR); \
	fi

install: venv
	$(PIP) install -e .[dev]

test: install
	$(PYTEST)

run: install
	$(UVICORN) app.main:app --reload

clean:
	rm -rf $(VENV_DIR)
