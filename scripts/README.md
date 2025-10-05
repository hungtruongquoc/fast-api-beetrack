# FastAPI Bee - Scripts Documentation

This directory contains utility scripts for running, testing, and managing the FastAPI Bee application.

## 📜 Available Scripts

### `run.sh` - Main Run Script

A comprehensive bash script that provides convenient commands for all common development tasks.

#### Features

- ✅ **Automatic virtual environment activation**
- ✅ **Poetry integration**
- ✅ **Colored output for better readability**
- ✅ **Error handling and validation**
- ✅ **30+ commands for all common tasks**

#### Usage

```bash
./scripts/run.sh [command]
```

## 📋 Command Reference

### Application Commands

| Command | Description | Example |
|---------|-------------|---------|
| `dev` | Start development server with auto-reload | `./scripts/run.sh dev` |
| `start` | Alias for `dev` | `./scripts/run.sh start` |
| `dev-host` | Start dev server on all interfaces (0.0.0.0) | `./scripts/run.sh dev-host` |
| `dev-port` | Start dev server on custom port | `PORT=3000 ./scripts/run.sh dev-port` |
| `prod` | Start production server with multiple workers | `./scripts/run.sh prod` |
| | | `WORKERS=8 ./scripts/run.sh prod` |

### Testing Commands

| Command | Description | Example |
|---------|-------------|---------|
| `test` | Run all tests with verbose output | `./scripts/run.sh test` |
| `test-fast` | Run all tests (minimal output) | `./scripts/run.sh test-fast` |
| `test-main` | Run tests for main application | `./scripts/run.sh test-main` |
| `test-api` | Run tests for API endpoints | `./scripts/run.sh test-api` |
| `test-schemas` | Run tests for schemas | `./scripts/run.sh test-schemas` |
| `test-core` | Run tests for core module | `./scripts/run.sh test-core` |
| `test-cov` | Run tests with coverage report | `./scripts/run.sh test-cov` |
| `test-cov-html` | Run tests with HTML coverage report | `./scripts/run.sh test-cov-html` |
| `test-watch` | Run tests in watch mode (stop on first failure) | `./scripts/run.sh test-watch` |

### Code Quality Commands

| Command | Description | Example |
|---------|-------------|---------|
| `format` | Format code with Black | `./scripts/run.sh format` |
| `format-check` | Check code formatting without changes | `./scripts/run.sh format-check` |
| `lint` | Run Flake8 linter | `./scripts/run.sh lint` |
| `typecheck` | Run MyPy type checker | `./scripts/run.sh typecheck` |
| `quality` | Run all quality checks (format, lint, typecheck, test) | `./scripts/run.sh quality` |

### Dependency Commands

| Command | Description | Example |
|---------|-------------|---------|
| `install` | Install all dependencies | `./scripts/run.sh install` |
| `install-dev` | Install with dev dependencies | `./scripts/run.sh install-dev` |
| `update` | Update all dependencies | `./scripts/run.sh update` |
| `show` | Show installed packages | `./scripts/run.sh show` |
| `show-tree` | Show dependency tree | `./scripts/run.sh show-tree` |

### Utility Commands

| Command | Description | Example |
|---------|-------------|---------|
| `clean` | Clean cache and temporary files | `./scripts/run.sh clean` |
| `shell` | Open Poetry shell | `./scripts/run.sh shell` |
| `info` | Show project information | `./scripts/run.sh info` |
| `health` | Check application health endpoint | `./scripts/run.sh health` |
| `help` | Show help message with all commands | `./scripts/run.sh help` |

## 🎯 Common Workflows

### Starting Development

```bash
# 1. Start the development server
./scripts/run.sh dev

# 2. In another terminal, run tests
./scripts/run.sh test

# 3. Check application health
./scripts/run.sh health
```

### Before Committing Code

```bash
# Run all quality checks
./scripts/run.sh quality

# This will:
# 1. Format code with Black
# 2. Run Flake8 linter
# 3. Run MyPy type checker
# 4. Run all tests
```

### Running Specific Tests

```bash
# Test only API endpoints
./scripts/run.sh test-api

# Test only schemas
./scripts/run.sh test-schemas

# Test with coverage
./scripts/run.sh test-cov-html
# Then open htmlcov/index.html
```

### Cleaning Up

```bash
# Clean all cache and temporary files
./scripts/run.sh clean

# This removes:
# - __pycache__ directories
# - .pyc, .pyo, .pyd files
# - .pytest_cache
# - .mypy_cache
# - htmlcov
# - .coverage files
```

### Checking Dependencies

```bash
# Show all installed packages
./scripts/run.sh show

# Show dependency tree
./scripts/run.sh show-tree

# Update all dependencies
./scripts/run.sh update
```

## 🔧 Environment Variables

The scripts support several environment variables for customization:

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `PORT` | Port for development server | 8000 | `PORT=3000 ./scripts/run.sh dev-port` |
| `WORKERS` | Number of workers for production | 4 | `WORKERS=8 ./scripts/run.sh prod` |

## 🎨 Output Colors

The script uses colored output for better readability:

- 🔵 **Blue (ℹ)** - Informational messages
- 🟢 **Green (✓)** - Success messages
- 🔴 **Red (✗)** - Error messages
- 🟡 **Yellow (⚠)** - Warning messages
- 🟣 **Magenta** - Section headers

## 🐛 Troubleshooting

### Script Permission Denied

```bash
# Make the script executable
chmod +x scripts/run.sh
```

### Virtual Environment Not Found

```bash
# Create virtual environment
python3 -m venv venv

# Then run the script
./scripts/run.sh dev
```

### Poetry Not Found

```bash
# Install Poetry
pip install poetry

# Verify installation
poetry --version
```

### Command Not Working

```bash
# Check available commands
./scripts/run.sh help

# Check if virtual environment is activated
echo $VIRTUAL_ENV

# Manually activate if needed
source venv/bin/activate
```

## 📚 Additional Resources

- [Main README](../README.md) - Complete project documentation
- [Makefile](../Makefile) - Alternative quick commands
- [Poetry Documentation](https://python-poetry.org/docs/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

## 🤝 Contributing

When adding new commands to the script:

1. Add the function in the appropriate section
2. Add the command to the `main()` function's case statement
3. Update the `show_usage()` function with the new command
4. Update this README with the new command
5. Test the command thoroughly

## 📝 Notes

- The script automatically activates the virtual environment if not already active
- All commands check for Poetry installation before running
- Error handling ensures the script exits cleanly on failures
- The script uses `set -e` to exit on any error

---

**For more information, run:** `./scripts/run.sh help`

