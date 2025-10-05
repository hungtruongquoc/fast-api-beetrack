#!/bin/bash

# FastAPI Bee - Run Script
# This script provides convenient commands for running the application and tests

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Function to print colored messages
print_info() {
    echo -e "${BLUE}ℹ ${NC}$1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_header() {
    echo -e "\n${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${MAGENTA}  $1${NC}"
    echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

# Function to check if virtual environment is activated
check_venv() {
    if [[ -z "$VIRTUAL_ENV" ]]; then
        print_warning "Virtual environment not activated"
        print_info "Activating virtual environment..."
        if [[ -f "venv/bin/activate" ]]; then
            source venv/bin/activate
            print_success "Virtual environment activated"
        else
            print_error "Virtual environment not found. Please run: python3 -m venv venv"
            exit 1
        fi
    else
        print_success "Virtual environment is active: $VIRTUAL_ENV"
    fi
}

# Function to check if Poetry is installed
check_poetry() {
    if ! command -v poetry &> /dev/null; then
        print_error "Poetry is not installed"
        print_info "Install Poetry with: pip install poetry"
        exit 1
    fi
    print_success "Poetry is installed: $(poetry --version)"
}

# Function to show usage
show_usage() {
    cat << EOF
${CYAN}FastAPI Bee - Run Script${NC}

${YELLOW}Usage:${NC}
  ./scripts/run.sh [command]

${YELLOW}Application Commands:${NC}
  ${GREEN}dev${NC}              Start development server with auto-reload
  ${GREEN}dev-host${NC}         Start dev server on all interfaces (0.0.0.0)
  ${GREEN}dev-port${NC}         Start dev server on custom port (specify PORT env var)
  ${GREEN}prod${NC}             Start production server with multiple workers
  ${GREEN}start${NC}            Alias for 'dev'

${YELLOW}Testing Commands:${NC}
  ${GREEN}test${NC}             Run all tests with verbose output
  ${GREEN}test-fast${NC}        Run all tests (minimal output)
  ${GREEN}test-main${NC}        Run tests for main application
  ${GREEN}test-api${NC}         Run tests for API endpoints
  ${GREEN}test-schemas${NC}     Run tests for schemas
  ${GREEN}test-core${NC}        Run tests for core module
  ${GREEN}test-cov${NC}         Run tests with coverage report
  ${GREEN}test-cov-html${NC}    Run tests with HTML coverage report
  ${GREEN}test-watch${NC}       Run tests in watch mode (stop on first failure)

${YELLOW}Code Quality Commands:${NC}
  ${GREEN}format${NC}           Format code with Black
  ${GREEN}format-check${NC}    Check code formatting without changes
  ${GREEN}lint${NC}             Run Flake8 linter
  ${GREEN}typecheck${NC}        Run MyPy type checker
  ${GREEN}quality${NC}          Run all quality checks (format, lint, typecheck, test)

${YELLOW}Dependency Commands:${NC}
  ${GREEN}install${NC}          Install all dependencies
  ${GREEN}install-dev${NC}     Install with dev dependencies
  ${GREEN}update${NC}           Update all dependencies
  ${GREEN}show${NC}             Show installed packages
  ${GREEN}show-tree${NC}        Show dependency tree

${YELLOW}Utility Commands:${NC}
  ${GREEN}clean${NC}            Clean cache and temporary files
  ${GREEN}shell${NC}            Open Poetry shell
  ${GREEN}info${NC}             Show project information
  ${GREEN}health${NC}           Check application health endpoint
  ${GREEN}help${NC}             Show this help message

${YELLOW}Examples:${NC}
  ./scripts/run.sh dev              # Start development server
  ./scripts/run.sh test             # Run all tests
  ./scripts/run.sh quality          # Run all quality checks
  PORT=3000 ./scripts/run.sh dev-port  # Start on port 3000

EOF
}

# Function to run development server
run_dev() {
    print_header "Starting Development Server"
    check_venv
    check_poetry
    print_info "Server will start at: http://localhost:8000"
    print_info "API Docs available at: http://localhost:8000/docs"
    print_info "Press Ctrl+C to stop"
    echo ""
    poetry run uvicorn app.main:app --reload
}

# Function to run development server on all interfaces
run_dev_host() {
    print_header "Starting Development Server (All Interfaces)"
    check_venv
    check_poetry
    print_info "Server will start at: http://0.0.0.0:8000"
    print_info "Press Ctrl+C to stop"
    echo ""
    poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
}

# Function to run development server on custom port
run_dev_port() {
    local port=${PORT:-8000}
    print_header "Starting Development Server on Port $port"
    check_venv
    check_poetry
    print_info "Server will start at: http://localhost:$port"
    print_info "API Docs available at: http://localhost:$port/docs"
    print_info "Press Ctrl+C to stop"
    echo ""
    poetry run uvicorn app.main:app --reload --port "$port"
}

# Function to run production server
run_prod() {
    print_header "Starting Production Server"
    check_venv
    check_poetry
    local workers=${WORKERS:-4}
    print_info "Starting with $workers workers"
    print_info "Server will start at: http://0.0.0.0:8000"
    print_info "Press Ctrl+C to stop"
    echo ""
    poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers "$workers"
}

# Function to run all tests
run_test() {
    print_header "Running All Tests"
    check_venv
    check_poetry
    poetry run pytest tests/ -v --tb=short --color=yes
    print_success "All tests completed!"
}

# Function to run tests (fast mode)
run_test_fast() {
    print_header "Running Tests (Fast Mode)"
    check_venv
    check_poetry
    poetry run pytest tests/ --tb=short --color=yes
}

# Function to run main tests
run_test_main() {
    print_header "Running Main Application Tests"
    check_venv
    check_poetry
    poetry run pytest tests/test_main.py -v --color=yes
}

# Function to run API tests
run_test_api() {
    print_header "Running API Tests"
    check_venv
    check_poetry
    poetry run pytest tests/api/ -v --color=yes
}

# Function to run schema tests
run_test_schemas() {
    print_header "Running Schema Tests"
    check_venv
    check_poetry
    poetry run pytest tests/schemas/ -v --color=yes
}

# Function to run core tests
run_test_core() {
    print_header "Running Core Tests"
    check_venv
    check_poetry
    poetry run pytest tests/core/ -v --color=yes
}

# Function to run tests with coverage
run_test_coverage() {
    print_header "Running Tests with Coverage"
    check_venv
    check_poetry
    poetry run pytest tests/ --cov=app --cov-report=term --cov-report=xml --color=yes
    print_success "Coverage report generated!"
}

# Function to run tests with HTML coverage
run_test_coverage_html() {
    print_header "Running Tests with HTML Coverage"
    check_venv
    check_poetry
    poetry run pytest tests/ --cov=app --cov-report=html --color=yes
    print_success "HTML coverage report generated in htmlcov/"
    print_info "Open htmlcov/index.html in your browser to view the report"
}

# Function to run tests in watch mode
run_test_watch() {
    print_header "Running Tests in Watch Mode"
    check_venv
    check_poetry
    print_info "Tests will stop on first failure"
    print_info "Press Ctrl+C to stop"
    echo ""
    poetry run pytest tests/ -v --tb=short -x --color=yes
}

# Function to format code
run_format() {
    print_header "Formatting Code with Black"
    check_venv
    check_poetry
    poetry run black app/ tests/
    print_success "Code formatted successfully!"
}

# Function to check formatting
run_format_check() {
    print_header "Checking Code Formatting"
    check_venv
    check_poetry
    poetry run black --check app/ tests/
    print_success "Code formatting is correct!"
}

# Function to run linter
run_lint() {
    print_header "Running Flake8 Linter"
    check_venv
    check_poetry
    poetry run flake8 app/ tests/
    print_success "Linting completed!"
}

# Function to run type checker
run_typecheck() {
    print_header "Running MyPy Type Checker"
    check_venv
    check_poetry
    poetry run mypy app/
    print_success "Type checking completed!"
}

# Function to run all quality checks
run_quality() {
    print_header "Running All Quality Checks"
    check_venv
    check_poetry
    
    print_info "Step 1/4: Formatting code..."
    poetry run black app/ tests/
    print_success "Formatting completed!"
    echo ""
    
    print_info "Step 2/4: Running linter..."
    poetry run flake8 app/ tests/
    print_success "Linting completed!"
    echo ""
    
    print_info "Step 3/4: Type checking..."
    poetry run mypy app/
    print_success "Type checking completed!"
    echo ""
    
    print_info "Step 4/4: Running tests..."
    poetry run pytest tests/ -v --tb=short --color=yes
    print_success "Tests completed!"
    echo ""
    
    print_success "All quality checks passed! ✨"
}

# Function to install dependencies
run_install() {
    print_header "Installing Dependencies"
    check_venv
    check_poetry
    poetry install
    print_success "Dependencies installed successfully!"
}

# Function to install with dev dependencies
run_install_dev() {
    print_header "Installing Dependencies (with dev)"
    check_venv
    check_poetry
    poetry install --with dev
    print_success "Dependencies installed successfully!"
}

# Function to update dependencies
run_update() {
    print_header "Updating Dependencies"
    check_venv
    check_poetry
    poetry update
    print_success "Dependencies updated successfully!"
}

# Function to show installed packages
run_show() {
    print_header "Installed Packages"
    check_venv
    check_poetry
    poetry show
}

# Function to show dependency tree
run_show_tree() {
    print_header "Dependency Tree"
    check_venv
    check_poetry
    poetry show --tree
}

# Function to clean cache and temporary files
run_clean() {
    print_header "Cleaning Cache and Temporary Files"
    
    print_info "Removing Python cache files..."
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
    find . -type f -name "*.pyo" -delete 2>/dev/null || true
    find . -type f -name "*.pyd" -delete 2>/dev/null || true
    
    print_info "Removing pytest cache..."
    rm -rf .pytest_cache 2>/dev/null || true
    
    print_info "Removing coverage files..."
    rm -rf htmlcov 2>/dev/null || true
    rm -f .coverage 2>/dev/null || true
    rm -f coverage.xml 2>/dev/null || true
    
    print_info "Removing mypy cache..."
    rm -rf .mypy_cache 2>/dev/null || true
    
    print_success "Cleanup completed!"
}

# Function to open Poetry shell
run_shell() {
    print_header "Opening Poetry Shell"
    check_venv
    check_poetry
    poetry shell
}

# Function to show project info
run_info() {
    print_header "Project Information"
    check_venv
    check_poetry
    
    echo -e "${CYAN}Project:${NC} FastAPI Bee"
    echo -e "${CYAN}Python:${NC} $(python --version)"
    echo -e "${CYAN}Poetry:${NC} $(poetry --version)"
    echo -e "${CYAN}Virtual Env:${NC} $VIRTUAL_ENV"
    echo ""
    
    print_info "Installed packages:"
    poetry show --no-dev | head -10
    echo ""
    
    print_info "Project structure:"
    tree -L 2 -I 'venv|__pycache__|*.pyc|.pytest_cache|.mypy_cache|htmlcov' || ls -la
}

# Function to check health endpoint
run_health() {
    print_header "Checking Application Health"
    
    if command -v curl &> /dev/null; then
        print_info "Checking http://localhost:8000/health"
        response=$(curl -s http://localhost:8000/health 2>/dev/null || echo "")
        
        if [[ -n "$response" ]]; then
            echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
            print_success "Application is healthy!"
        else
            print_error "Application is not running or not responding"
            print_info "Start the application with: ./scripts/run.sh dev"
        fi
    else
        print_error "curl is not installed"
        print_info "Install curl or check manually: http://localhost:8000/health"
    fi
}

# Main script logic
main() {
    local command=${1:-help}
    
    case "$command" in
        dev|start)
            run_dev
            ;;
        dev-host)
            run_dev_host
            ;;
        dev-port)
            run_dev_port
            ;;
        prod)
            run_prod
            ;;
        test)
            run_test
            ;;
        test-fast)
            run_test_fast
            ;;
        test-main)
            run_test_main
            ;;
        test-api)
            run_test_api
            ;;
        test-schemas)
            run_test_schemas
            ;;
        test-core)
            run_test_core
            ;;
        test-cov)
            run_test_coverage
            ;;
        test-cov-html)
            run_test_coverage_html
            ;;
        test-watch)
            run_test_watch
            ;;
        format)
            run_format
            ;;
        format-check)
            run_format_check
            ;;
        lint)
            run_lint
            ;;
        typecheck)
            run_typecheck
            ;;
        quality)
            run_quality
            ;;
        install)
            run_install
            ;;
        install-dev)
            run_install_dev
            ;;
        update)
            run_update
            ;;
        show)
            run_show
            ;;
        show-tree)
            run_show_tree
            ;;
        clean)
            run_clean
            ;;
        shell)
            run_shell
            ;;
        info)
            run_info
            ;;
        health)
            run_health
            ;;
        help|--help|-h)
            show_usage
            ;;
        *)
            print_error "Unknown command: $command"
            echo ""
            show_usage
            exit 1
            ;;
    esac
}

# Run main function
main "$@"

