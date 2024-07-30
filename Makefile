SHELL := /bin/bash

.PHONY: clean lint

APP_PACKAGE := "./src/qna_web"

clean:
	@find . -name "*.pyc" -exec rm -rf {} \;
	@find . -name "__pycache__" -delete

black:
	black --check $(APP_PACKAGE)

black-fmt:
	black $(APP_PACKAGE)

flake:
	flake8 $(APP_PACKAGE)

mypy:
	mypy $(APP_PACKAGE) --install-types --non-interactive

isort:
	isort --check --quiet $(APP_PACKAGE)

isort-fmt:
	isort $(APP_PACKAGE)

fmt: black-fmt isort-fmt
	@echo "Code formatted"

lint: black flake isort mypy
	@echo "Lint checks passed"
