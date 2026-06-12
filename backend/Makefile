.PHONY: install test test-cov run lint format

install:
	pip install -e ".[dev]"

test:
	python -m pytest tests/ -v

test-cov:
	python -m pytest tests/ -v --cov=src --cov-report=term-missing

run:
	python -m uvicorn src.main:app --reload

lint:
	python -m ruff check src/

format:
	python -m ruff format src/
