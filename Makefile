.DEFAULT_GOAL := all

API_DEMO_CONTAINER_NAME := api-demo
API_DEMO_IMAGE_NAME := api-demo

app_root = app
pkg_src = $(app_root)/app
tests_src = $(app_root)/tests
local_tests_src = $(app_root)/tests/local

isort = isort -rc $(pkg_src) $(tests_src)
black = black $(pkg_src) $(tests_src)
flake8 = flake8 $(pkg_src) $(tests_src)

.PHONY: all
all: build run

.PHONY: format
format:
	$(isort)
	$(black)

.PHONY: lint
lint:
	$(flake8)

.PHONY: test-local
test-local:
	pytest $(local_tests_src) --cov=$(pkg_src)

.PHONY: test-dev
test-dev:
	./scripts/test-dev.sh

.PHONY: build
test-dev:
	./scripts/build.sh

.PHONY: run
test-dev:
	./scripts/run.sh

.PHONY: stop
test-dev:
	./scripts/stop.sh

.PHONY: clean
clean:
	docker stop $(API_DEMO_CONTAINER_NAME)
	docker rmi $(API_DEMO_IMAGE_NAME)
	rm -rf `find . -name __pycache__`
	rm -f `find . -type f -name '*.py[co]' `
	rm -f `find . -type f -name '*~' `
	rm -f `find . -type f -name '.*~' `
	rm -rf `find . -type d -name '*.egg-info' `
	rm -rf `find . -type d -name 'pip-wheel-metadata' `
	rm -rf .cache
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf htmlcov
	rm -rf *.egg-info
	rm -f .coverage
	rm -f .coverage.*
	rm -rf build