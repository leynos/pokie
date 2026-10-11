MDLINT ?= markdownlint-cli2
NIXIE ?= nixie
MDTABLEFIX ?= mdtablefix
MDTABLEFIX_VERSION ?= 0.6.1
MDTABLEFIX_SELECT = --git --include-untracked
MDTABLEFIX_RULES = --wrap --renumber --breaks --ellipsis --fences
ACTIONLINT ?= actionlint
ACTION_VALIDATOR ?= action-validator
export PATH := $(HOME)/.local/bin:$(HOME)/.bun/bin:$(PATH)
UV ?= $(shell command -v uv 2>/dev/null || printf '%s/.local/bin/uv' "$$HOME")
USER_CARGO := $(HOME)/.cargo/bin/cargo
USER_WHITAKER := $(HOME)/.local/bin/whitaker
USER_BIN_PATH := $(HOME)/.cargo/bin:$(HOME)/.local/bin:$(HOME)/.bun/bin
TOOLS = $(MDTABLEFIX) $(MDLINT) $(ACTIONLINT) $(ACTION_VALIDATOR)
VENV_TOOLS = pytest
UV_ENV = PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1 UV_CACHE_DIR=.uv-cache UV_TOOL_DIR=.uv-tools
TYPOS_CONFIG_BUILDER_VERSION ?= v0.1.2
TYPOS_CONFIG_BUILDER = env $(UV_ENV) $(UV) tool run --python 3.14 --from \
	"git+https://github.com/leynos/typos-config-builder.git@$(TYPOS_CONFIG_BUILDER_VERSION)" \
	typos-config-builder
WITH_ACT ?= 0
ACT_IMAGE ?= ghcr.io/catthehacker/ubuntu:act-24.04
PYTEST_XDIST_WORKERS ?= auto
# Include tracked and new source anywhere, including hidden action directories.
PYTHON_TARGETS ?= $(shell git ls-files --cached --others --exclude-standard '*.py' '*.pyi')
RUFF_VERSION ?= 0.16.8
TY_VERSION ?= 0.0.56
RUFF = $(UV_ENV) $(UV) tool run --python 3.14 --from 'ruff==$(RUFF_VERSION)' ruff
TY = $(UV_ENV) $(UV) tool run --python 3.14 --from 'ty==$(TY_VERSION)' ty
DF12_PYTHON_LINTS_REF ?= v0.4.0
DF12_PYTHON_LINTS = git+https://github.com/leynos/df12-python-lints.git@$(DF12_PYTHON_LINTS_REF)
DF12_PYLINT_MESSAGES = R9101,C9102,R9103,R9104,C9105,C9106,C9107,R9108,R9109,R9110,R9111,R9112,C9112
DF12_PYLINT = $(UV_ENV) $(UV) run pylint --disable=all --load-plugins=df12_python_lints --enable=$(DF12_PYLINT_MESSAGES)
AMBRLEAKS = $(UV_ENV) $(UV) run ambrleaks
SKYLOS = $(UV_ENV) $(UV) tool run --python 3.14 --from 'df12-python-lints[skylos] @ $(DF12_PYTHON_LINTS)' df12-skylos
DUPLICATION_GATE = $(UV_ENV) $(UV) tool run --python 3.14 --from '$(DF12_PYTHON_LINTS)' df12-duplication
PYLINT_PYTHON ?= pypy@3.12
PYLINT_VERSION ?= 4.0.9
PYLINT_TARGETS ?= $(PYTHON_TARGETS)
PYLINT = $(UV_ENV) $(UV) tool run --managed-python --python $(PYLINT_PYTHON) --from 'pylint==$(PYLINT_VERSION)' pylint


.PHONY: help all audit clean build build-release lint lint-python fmt check-fmt \
        markdownlint nixie spelling test test-act typecheck validate lint-actions \
        install-nose duplication dead-code $(TOOLS) $(VENV_TOOLS)

.DEFAULT_GOAL := all
# Shared build caches require sequential gate execution, even with make -j.
.NOTPARALLEL:

all: build check-fmt lint typecheck test markdownlint nixie audit validate

define ensure_uv
	@command -v $(UV) >/dev/null 2>&1 || { \
	  printf "Error: uv is required, but '%s' was not found or is not executable\n" "$(UV)" >&2; \
	  exit 1; \
	}
endef

.venv: pyproject.toml
	$(call ensure_uv)
	$(UV_ENV) $(UV) venv --clear

build: .venv ## Build virtual-env and install deps
	$(UV_ENV) $(UV) sync --group dev

build-release: ## Build artefacts (sdist & wheel)
	$(call ensure_uv)
	$(UV_ENV) $(UV) run python -m build --sdist --wheel

clean: ## Remove build artefacts
	rm -rf build dist *.egg-info \
	  .mypy_cache .pytest_cache .coverage coverage.* \
	  lcov.info htmlcov .venv .uv-cache .uv-tools \
	  .typos-oxendict-base.json .typos-oxendict-base.toml
	find . -type d -name '__pycache__' -print0 | xargs -0 -r rm -rf

define ensure_tool
	@command -v $(1) >/dev/null 2>&1 || { \
	  printf "Error: '%s' is required, but not installed\n" "$(1)" >&2; \
	  exit 1; \
	}
endef

define ensure_tool_venv
	@$(UV_ENV) $(UV) run which $(1) >/dev/null 2>&1 || { \
	  printf "Error: '%s' is required in the virtualenv, but is not installed\n" "$(1)" >&2; \
	  exit 1; \
	}
endef

ifneq ($(strip $(TOOLS)),)
$(TOOLS): ## Verify required CLI tools
	$(call ensure_tool,$@)
endif


ifneq ($(strip $(VENV_TOOLS)),)
.PHONY: $(VENV_TOOLS)
$(VENV_TOOLS): build ## Verify required CLI tools in venv
	$(call ensure_tool_venv,$@)
endif


fmt: build $(MDTABLEFIX) ## Format sources
	$(RUFF) format $(PYTHON_TARGETS)
	$(RUFF) check --select I --fix $(PYTHON_TARGETS)

	$(MDTABLEFIX) --in-place $(MDTABLEFIX_SELECT) $(MDTABLEFIX_RULES)

check-fmt: build $(MDTABLEFIX) ## Verify formatting
	$(RUFF) format --check $(PYTHON_TARGETS)

	@test "$$($(MDTABLEFIX) --version)" = "mdtablefix $(MDTABLEFIX_VERSION)" || { \
	  printf 'Error: mdtablefix %s is required\n' '$(MDTABLEFIX_VERSION)' >&2; exit 1; \
	}
	$(MDTABLEFIX) --check $(MDTABLEFIX_SELECT) $(MDTABLEFIX_RULES)

lint: lint-python dead-code duplication lint-actions ## Run linters

lint-python: build ## Run Python linters
	$(RUFF) check $(PYTHON_TARGETS)
	$(UV_ENV) $(UV) run interrogate --fail-under 100 $(PYTHON_TARGETS)
	$(PYLINT) $(PYLINT_TARGETS)
	$(DF12_PYLINT) $(PYTHON_TARGETS)
	$(AMBRLEAKS) tests


typecheck: build ## Run typechecking
	$(TY) --version
	$(TY) check $(PYTHON_TARGETS)

audit: build ## Audit dependencies for known vulnerabilities
	$(UV_ENV) $(UV) run pip-audit


markdownlint: $(MDLINT) ## Lint Markdown files and spelling
	env -u NO_COLOR $(MDLINT) '**/*.md'
	+$(MAKE) spelling

spelling: ## Enforce en-GB-oxendict spelling
	$(TYPOS_CONFIG_BUILDER) gate --repository . --scope all

nixie: ## Validate Mermaid diagrams
	$(call ensure_tool,$(NIXIE))
	$(NIXIE) --no-sandbox

test: build $(VENV_TOOLS) ## Run tests
	$(UV_ENV) $(UV) run pytest -v -n $(PYTEST_XDIST_WORKERS)
	$(if $(filter 1 true yes on,$(WITH_ACT)),+$(MAKE) test-act,)

# Static workflow checks belong to lint-actions. act only exercises a wheel
# build and import, so it cannot recursively repeat the normal CI gates.
test-act: ## Exercise the pure-wheel action using act (requires Docker)
	act workflow_dispatch -W .github/workflows/act-smoke.yml -j pure-wheel \
	  -P "ubuntu-latest=$(ACT_IMAGE)"

validate: ## Validate the Makefile
	mbake validate Makefile

dead-code: ## Run the shared strict Skylos gate
	$(SKYLOS) check --repository .
	$(UV_ENV) $(UV) run vulture tests

install-nose: ## Install the pinned detector with the shared verified installer
	$(DUPLICATION_GATE) install --repository .

duplication: install-nose ## Check every duplication family with the shared gate
	$(DUPLICATION_GATE) check --repository .

lint-actions: build $(ACTIONLINT) $(ACTION_VALIDATOR) ## Validate workflows and local actions
	$(call ensure_tool,shellcheck)
	$(UV_ENV) $(UV) run yamllint --strict .github
	$(ACTIONLINT)
	@set -eu; workflow=$$(mktemp /tmp/pokie-action-XXXXXX.yml); \
	trap 'rm -f "$$workflow"' EXIT; find .github/actions -type f \( -name action.yml -o -name action.yaml \) -print | \
	while IFS= read -r action; do \
	  $(ACTION_VALIDATOR) "$$action"; \
	  $(UV_ENV) $(UV) run python scripts/action_workflow.py "$$action" > "$$workflow"; \
	  $(ACTIONLINT) -stdin-filename "$$action" - < "$$workflow"; \
	done

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?##' $(MAKEFILE_LIST) | \
	awk 'BEGIN {FS=":.*##"; printf "Available targets:\n"} {gsub(/^[[:space:]]+/, "", $$2); printf "  %-20s %s\n", $$1, $$2}'
