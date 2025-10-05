# FastAPI Bee - Makefile
# Quick commands for common tasks

.PHONY: help dev test format lint typecheck quality install clean

# Default target
.DEFAULT_GOAL := help

# Colors
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[1;33m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(BLUE)FastAPI Bee - Available Commands$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)For more commands, use: ./scripts/run.sh help$(NC)"

# Application Commands
dev: ## Start development server
	@./scripts/run.sh dev

start: ## Alias for dev
	@./scripts/run.sh dev

prod: ## Start production server
	@./scripts/run.sh prod

# Testing Commands
test: ## Run all tests
	@./scripts/run.sh test

test-fast: ## Run tests (minimal output)
	@./scripts/run.sh test-fast

test-cov: ## Run tests with coverage
	@./scripts/run.sh test-cov

test-cov-html: ## Run tests with HTML coverage report
	@./scripts/run.sh test-cov-html

test-watch: ## Run tests in watch mode
	@./scripts/run.sh test-watch

test-main: ## Run main application tests
	@./scripts/run.sh test-main

test-api: ## Run API tests
	@./scripts/run.sh test-api

test-schemas: ## Run schema tests
	@./scripts/run.sh test-schemas

test-core: ## Run core tests
	@./scripts/run.sh test-core

# Code Quality Commands
format: ## Format code with Black
	@./scripts/run.sh format

format-check: ## Check code formatting
	@./scripts/run.sh format-check

lint: ## Run Flake8 linter
	@./scripts/run.sh lint

typecheck: ## Run MyPy type checker
	@./scripts/run.sh typecheck

quality: ## Run all quality checks
	@./scripts/run.sh quality

# Dependency Commands
install: ## Install dependencies
	@./scripts/run.sh install

update: ## Update dependencies
	@./scripts/run.sh update

show: ## Show installed packages
	@./scripts/run.sh show

# Utility Commands
clean: ## Clean cache and temporary files
	@./scripts/run.sh clean

shell: ## Open Poetry shell
	@./scripts/run.sh shell

info: ## Show project information
	@./scripts/run.sh info

health: ## Check application health
	@./scripts/run.sh health

# Combined Commands
check: format lint typecheck test ## Run format, lint, typecheck, and test

all: install quality ## Install dependencies and run quality checks

