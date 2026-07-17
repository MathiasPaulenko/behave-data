.PHONY: install dev lint lint-fix format format-check test test-cov clean build

install:
	pip install -e .

dev:
	pip install -e ".[dev,yaml,excel]"

lint:
	ruff check .

lint-fix:
	ruff check . --fix

format:
	ruff format .

format-check:
	ruff format --check .

test:
	pytest tests/ -v

test-cov:
	pytest tests/ -v --cov --cov-report=term-missing

clean:
	rm -rf dist/ build/ *.egg-info/ .coverage htmlcov/ .pytest_cache/ .ruff_cache/

build:
	python -m build
