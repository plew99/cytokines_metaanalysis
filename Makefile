\
# Makefile — pomocnicze skróty (venv + pip)
PYTHON=python
VENV=.venv
BIN=$(VENV)/bin
PIP=$(BIN)/pip

# Windows fallback (jeśli używasz PowerShell/cmd, uruchamiaj komendy z README)
OS := $(shell uname 2>/dev/null || echo Windows)

ifeq ($(OS), Windows)
BIN=$(VENV)/Scripts
PIP=$(BIN)/pip.exe
endif

.PHONY: venv install format lint test clean

venv:
	$(PYTHON) -m venv $(VENV)

install: venv
	$(BIN)/python -m pip install --upgrade pip
	$(PIP) install -r requirements.txt
	$(BIN)/pre-commit install

format:
	$(BIN)/black .

lint:
	$(BIN)/ruff check .

test:
	$(BIN)/pytest -q

clean:
	rm -rf $(VENV) __pycache__ .pytest_cache .ruff_cache
