# FastAPI Bee 🐝

A modern, production-ready FastAPI backend application with a clean architecture, comprehensive testing, and best practices.

## 🚀 Features

- ✅ **FastAPI** - Modern, fast web framework for building APIs
- ✅ **Pydantic v2** - Data validation using Python type annotations
- ✅ **Poetry** - Dependency management and packaging
- ✅ **Structured Architecture** - Clean, scalable project layout
- ✅ **API Versioning** - Built-in support for API versions (v1)
- ✅ **CORS Middleware** - Cross-Origin Resource Sharing configured
- ✅ **Auto-generated Documentation** - Interactive Swagger UI and ReDoc
- ✅ **Comprehensive Testing** - 54+ tests with pytest
- ✅ **Type Checking** - MyPy for static type analysis
- ✅ **Code Formatting** - Black for consistent code style
- ✅ **Linting** - Flake8 for code quality checks

## 📚 Technology Stack

### Core Framework
- **[FastAPI](https://fastapi.tiangolo.com/)** (v0.115+) - High-performance async web framework
  - Built on Starlette for web routing
  - Automatic OpenAPI documentation generation
  - Native async/await support
  - Dependency injection system

### Data Validation & Settings
- **[Pydantic](https://docs.pydantic.dev/)** (v2.9+) - Data validation using Python type hints
  - Runtime type checking
  - JSON schema generation
  - Settings management with environment variables
- **[Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)** (v2.6+) - Configuration management

### Server
- **[Uvicorn](https://www.uvicorn.org/)** (v0.32+) - Lightning-fast ASGI server
  - Hot reload for development
  - Production-ready performance
  - WebSocket support

### Development Tools
- **[Poetry](https://python-poetry.org/)** - Dependency management and packaging
- **[Pytest](https://pytest.org/)** (v8.3+) - Testing framework
- **[Pytest-asyncio](https://pytest-asyncio.readthedocs.io/)** - Async test support
- **[HTTPX](https://www.python-httpx.org/)** - HTTP client for testing
- **[Black](https://black.readthedocs.io/)** - Code formatter
- **[Flake8](https://flake8.pycqa.org/)** - Linting tool
- **[MyPy](https://mypy.readthedocs.io/)** - Static type checker

### Python Version
- **Python 3.9+** - Managed with pyenv

## ⚡ Quick Start

```bash
# 1. Clone and setup
git clone <repository-url>
cd fast-api-bee
python3 -m venv venv
source venv/bin/activate
pip install poetry
poetry install

# 2. Run the application
./scripts/run.sh dev
# or
make dev

# 3. Run tests
./scripts/run.sh test
# or
make test

# 4. View API docs
open http://localhost:8000/docs
```

## 🎯 Available Scripts

This project includes convenient scripts for all common tasks:

### Run Script (`./scripts/run.sh`)

A comprehensive bash script with 30+ commands:

```bash
# Application
./scripts/run.sh dev              # Start development server
./scripts/run.sh prod             # Start production server

# Testing
./scripts/run.sh test             # Run all tests
./scripts/run.sh test-cov         # Run tests with coverage
./scripts/run.sh test-api         # Run API tests only

# Code Quality
./scripts/run.sh format           # Format code with Black
./scripts/run.sh lint             # Run Flake8 linter
./scripts/run.sh typecheck        # Run MyPy type checker
./scripts/run.sh quality          # Run all quality checks

# Utilities
./scripts/run.sh clean            # Clean cache files
./scripts/run.sh health           # Check app health
./scripts/run.sh info             # Show project info
./scripts/run.sh help             # Show all commands
```

### Makefile

Quick shortcuts for common commands:

```bash
make dev                # Start development server
make test               # Run all tests
make quality            # Run all quality checks
make format             # Format code
make lint               # Run linter
make clean              # Clean cache
make help               # Show all commands
```

**Benefits:**
- ✅ **Automatic virtual environment activation**
- ✅ **Colored output for better readability**
- ✅ **Error handling and validation**
- ✅ **Consistent commands across team**
- ✅ **No need to remember complex Poetry commands**

## 📁 Project Structure

```
fast-api-bee/
│
├── app/                                    # Main application package
│   ├── __init__.py                        # Package initialization
│   ├── main.py                            # FastAPI app entry point & configuration
│   │
│   ├── api/                               # API layer (presentation)
│   │   ├── __init__.py
│   │   └── v1/                            # API version 1
│   │       ├── __init__.py
│   │       ├── router.py                  # Main API router (aggregates all endpoints)
│   │       └── endpoints/                 # API endpoints
│   │           ├── __init__.py
│   │           └── items.py               # Items CRUD endpoints
│   │
│   ├── services/                          # Business logic layer
│   │   ├── __init__.py
│   │   └── item_service.py                # Item business logic & operations
│   │
│   ├── core/                              # Core functionality
│   │   ├── __init__.py
│   │   └── config.py                      # Application settings & configuration
│   │
│   └── schemas/                           # Pydantic models (request/response schemas)
│       ├── __init__.py
│       └── item.py                        # Item schemas (Create, Update, Response)
│
├── tests/                                  # Test suite (mirrors app structure)
│   ├── __init__.py
│   ├── conftest.py                        # Pytest fixtures & configuration
│   ├── test_main.py                       # Tests for app/main.py (5 tests)
│   │
│   ├── api/                               # API tests
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── test_router.py             # Router configuration tests (3 tests)
│   │       └── endpoints/
│   │           ├── __init__.py
│   │           └── test_items.py          # Items endpoint tests (19 tests)
│   │
│   ├── services/                          # Service tests
│   │   ├── __init__.py
│   │   └── test_item_service.py           # Item service tests (23 tests)
│   │
│   ├── core/                              # Core tests
│   │   ├── __init__.py
│   │   └── test_config.py                 # Configuration tests (5 tests)
│   │
│   └── schemas/                           # Schema tests
│       ├── __init__.py
│       └── test_item.py                   # Item schema validation tests (25 tests)
│
├── venv/                                   # Virtual environment (excluded from git)
├── .env                                    # Environment variables (excluded from git)
├── .env.example                           # Example environment variables
├── .gitignore                             # Git ignore rules
├── pyproject.toml                         # Poetry dependencies & project config
├── poetry.lock                            # Locked dependency versions
└── README.md                              # This file
```

### Architecture Explanation

This project follows a **layered architecture** pattern with clear separation of concerns:

#### **app/main.py**
- FastAPI application instance
- Middleware configuration (CORS)
- Router registration
- Root and health check endpoints

#### **app/api/v1/** (Presentation Layer)
- API version 1 implementation
- `router.py` aggregates all endpoint routers
- `endpoints/` contains individual resource endpoints
- Handles HTTP requests/responses
- Uses dependency injection to access services
- Easy to add v2, v3, etc. in the future

#### **app/services/** (Business Logic Layer)
- Contains business logic and operations
- `item_service.py` manages item operations
- Independent of HTTP/API concerns
- Can be reused across different endpoints
- Easier to test in isolation
- Implements patterns like singleton for shared state

#### **app/core/**
- Core application functionality
- `config.py` manages settings using Pydantic Settings
- Loads configuration from environment variables

#### **app/schemas/**
- Pydantic models for request/response validation
- Separate schemas for Create, Update, and Response
- Automatic JSON schema generation for OpenAPI docs
- Used by both API and service layers

#### **tests/**
- Mirrors the app structure for easy navigation
- Unit tests for services (business logic)
- Unit tests for schemas and configuration
- Integration tests for API endpoints
- Fixtures in `conftest.py` for reusable test data

### Layered Architecture Benefits

```
┌─────────────────────────────────────┐
│   API Layer (app/api/)              │  ← HTTP requests/responses
│   - Endpoints                       │  ← Request validation
│   - Routing                         │  ← Response formatting
└─────────────────────────────────────┘
              ↓ uses
┌─────────────────────────────────────┐
│   Service Layer (app/services/)     │  ← Business logic
│   - ItemService                     │  ← Data operations
│   - Business rules                  │  ← Filtering, searching
└─────────────────────────────────────┘
              ↓ uses
┌─────────────────────────────────────┐
│   Schema Layer (app/schemas/)       │  ← Data validation
│   - Pydantic models                 │  ← Type checking
│   - Validation rules                │  ← Serialization
└─────────────────────────────────────┘
```

**Benefits:**
- ✅ **Separation of Concerns** - Each layer has a single responsibility
- ✅ **Testability** - Easy to test business logic independently
- ✅ **Reusability** - Services can be used by multiple endpoints
- ✅ **Maintainability** - Changes in one layer don't affect others
- ✅ **Scalability** - Easy to add new features or layers

## 🛠️ Setup & Installation

### Prerequisites

- **Python 3.9+** (managed with pyenv recommended)
- **Poetry** for dependency management
- **Git** for version control

### Initial Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd fast-api-bee
   ```

2. **Create virtual environment:**
   ```bash
   python3 -m venv venv
   ```

3. **Activate virtual environment:**
   ```bash
   # On macOS/Linux
   source venv/bin/activate

   # On Windows
   venv\Scripts\activate
   ```

4. **Install Poetry (if not already installed):**
   ```bash
   pip install poetry
   ```

5. **Install dependencies:**
   ```bash
   poetry install
   ```

6. **Create environment file:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

## 🚀 Running the Application

### Quick Start with Scripts

We provide convenient scripts for all common tasks:

**Using the run script (Recommended):**
```bash
# Start development server
./scripts/run.sh dev

# Run all tests
./scripts/run.sh test

# Run all quality checks
./scripts/run.sh quality

# See all available commands
./scripts/run.sh help
```

**Using Makefile (Alternative):**
```bash
# Start development server
make dev

# Run all tests
make test

# Run all quality checks
make quality

# See all available commands
make help
```

### Development Server

**Option 1: Using the run script (Easiest)**
```bash
./scripts/run.sh dev
```

**Option 2: Using Makefile**
```bash
make dev
```

**Option 3: Using Poetry directly**
```bash
source venv/bin/activate
poetry run uvicorn app.main:app --reload
```

**Option 4: Custom port**
```bash
PORT=3000 ./scripts/run.sh dev-port
```

**Option 5: All interfaces (0.0.0.0)**
```bash
./scripts/run.sh dev-host
```

### Production Server

```bash
# Using run script (4 workers by default)
./scripts/run.sh prod

# Using Poetry with custom workers
WORKERS=8 ./scripts/run.sh prod

# Direct command
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Access Points

Once the server is running, you can access:

- **API Base URL**: http://localhost:8000
- **Interactive API Docs (Swagger UI)**: http://localhost:8000/docs
- **Alternative API Docs (ReDoc)**: http://localhost:8000/redoc
- **OpenAPI Schema (JSON)**: http://localhost:8000/api/v1/openapi.json
- **Health Check**: http://localhost:8000/health

### Check Application Health

```bash
# Using run script
./scripts/run.sh health

# Using Makefile
make health

# Using curl directly
curl http://localhost:8000/health
```

## 📡 API Endpoints

### Root Endpoints

| Method | Endpoint | Description | Response |
|--------|----------|-------------|----------|
| `GET` | `/` | Welcome message | JSON with app info |
| `GET` | `/health` | Health check | `{"status": "healthy"}` |

### Items API (v1)

| Method | Endpoint | Description | Request Body | Response |
|--------|----------|-------------|--------------|----------|
| `GET` | `/api/v1/items/` | Get all items | - | Array of items |
| `GET` | `/api/v1/items/{item_id}` | Get specific item | - | Item object |
| `POST` | `/api/v1/items/` | Create new item | ItemCreate | Item object (201) |
| `PUT` | `/api/v1/items/{item_id}` | Update item | ItemUpdate | Item object |
| `DELETE` | `/api/v1/items/{item_id}` | Delete item | - | No content (204) |

### Example API Requests

**Create an item:**
```bash
curl -X POST "http://localhost:8000/api/v1/items/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Sample Item",
    "description": "This is a sample item",
    "price": 29.99,
    "is_available": true
  }'
```

**Get all items:**
```bash
curl http://localhost:8000/api/v1/items/
```

**Get specific item:**
```bash
curl http://localhost:8000/api/v1/items/1
```

**Update an item:**
```bash
curl -X PUT "http://localhost:8000/api/v1/items/1" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated Item",
    "price": 39.99
  }'
```

**Delete an item:**
```bash
curl -X DELETE http://localhost:8000/api/v1/items/1
```

## 🧪 Testing

### Quick Test Commands

**Using the run script (Recommended):**
```bash
# Run all tests
./scripts/run.sh test

# Run tests (fast mode, minimal output)
./scripts/run.sh test-fast

# Run tests with coverage
./scripts/run.sh test-cov

# Run tests with HTML coverage report
./scripts/run.sh test-cov-html

# Run tests in watch mode (stops on first failure)
./scripts/run.sh test-watch
```

**Using Makefile:**
```bash
make test              # Run all tests
make test-fast         # Fast mode
make test-cov          # With coverage
make test-cov-html     # HTML coverage report
```

### Run Specific Test Modules

**Using the run script:**
```bash
# Test main application
./scripts/run.sh test-main

# Test API endpoints
./scripts/run.sh test-api

# Test schemas
./scripts/run.sh test-schemas

# Test core configuration
./scripts/run.sh test-core
```

**Using Makefile:**
```bash
make test-main         # Main application tests
make test-api          # API tests
make test-schemas      # Schema tests
make test-core         # Core tests
```

### Run Specific Tests (Poetry)

```bash
# Test specific file
poetry run pytest tests/test_main.py -v

# Test specific module
poetry run pytest tests/api/v1/endpoints/test_items.py -v

# Test specific directory
poetry run pytest tests/schemas/ -v

# Test specific function
poetry run pytest tests/test_main.py::test_read_root -v

# Test specific class
poetry run pytest tests/api/v1/endpoints/test_items.py::TestItemsAPI -v
```

### Run Tests by Pattern

```bash
# Run all tests matching "item"
poetry run pytest tests/ -k "item" -v

# Run all validation tests
poetry run pytest tests/ -k "validation" -v

# Run all tests except slow ones
poetry run pytest tests/ -m "not slow" -v
```

### Test Coverage

**Using the run script:**
```bash
# Terminal coverage report
./scripts/run.sh test-cov

# HTML coverage report (opens in browser)
./scripts/run.sh test-cov-html
# Then open: htmlcov/index.html
```

**Using Poetry directly:**
```bash
# Generate HTML coverage report
poetry run pytest tests/ --cov=app --cov-report=html

# View coverage in terminal
poetry run pytest tests/ --cov=app --cov-report=term

# Generate XML coverage report (for CI/CD)
poetry run pytest tests/ --cov=app --cov-report=xml
```

**Current Test Coverage:**
- **77 tests** across all modules
- **Main Application**: 5 tests
- **Core Configuration**: 5 tests
- **Schemas**: 25 tests
- **Services**: 23 tests (NEW!)
- **API Router**: 3 tests
- **API Endpoints**: 19 tests

## 🛠️ Development Tools

### Quick Quality Commands

**Using the run script (Recommended):**
```bash
# Format code with Black
./scripts/run.sh format

# Check formatting without changes
./scripts/run.sh format-check

# Run Flake8 linter
./scripts/run.sh lint

# Run MyPy type checker
./scripts/run.sh typecheck

# Run ALL quality checks (format + lint + typecheck + test)
./scripts/run.sh quality
```

**Using Makefile:**
```bash
make format            # Format code
make format-check      # Check formatting
make lint              # Run linter
make typecheck         # Type check
make quality           # All quality checks
make check             # Format + lint + typecheck + test
```

### Code Formatting with Black

**Using the run script:**
```bash
# Format all code
./scripts/run.sh format

# Check formatting only
./scripts/run.sh format-check
```

**Using Poetry directly:**
```bash
# Format all code in app directory
poetry run black app/

# Format all code in tests directory
poetry run black tests/

# Format entire project
poetry run black .

# Check formatting without making changes
poetry run black --check app/
```

### Linting with Flake8

**Using the run script:**
```bash
./scripts/run.sh lint
```

**Using Poetry directly:**
```bash
# Lint app directory
poetry run flake8 app/

# Lint tests directory
poetry run flake8 tests/

# Lint entire project
poetry run flake8 .
```

### Type Checking with MyPy

**Using the run script:**
```bash
./scripts/run.sh typecheck
```

**Using Poetry directly:**
```bash
# Type check app directory
poetry run mypy app/

# Type check specific file
poetry run mypy app/main.py

# Type check with verbose output
poetry run mypy app/ --verbose
```

### Run All Quality Checks

**Using the run script (Easiest):**
```bash
# Runs: format → lint → typecheck → test
./scripts/run.sh quality
```

**Using Makefile:**
```bash
# Runs: format → lint → typecheck → test
make quality

# Or use check (same as quality)
make check
```

**Using Poetry directly:**
```bash
# Format, lint, type check, and test
poetry run black . && \
poetry run flake8 . && \
poetry run mypy app/ && \
poetry run pytest tests/ -v
```

## 📦 Dependency Management

### Add New Dependencies

```bash
# Add production dependency
poetry add package-name

# Add development dependency
poetry add --group dev package-name

# Add specific version
poetry add "package-name==1.2.3"

# Add with version constraint
poetry add "package-name>=1.2.0,<2.0.0"
```

### Update Dependencies

```bash
# Update all dependencies
poetry update

# Update specific package
poetry update package-name

# Show outdated packages
poetry show --outdated
```

### View Dependencies

```bash
# List all installed packages
poetry show

# Show dependency tree
poetry show --tree

# Show specific package info
poetry show package-name
```

## ⚙️ Environment Variables

Create a `.env` file in the root directory to configure the application:

```env
# Application Settings
PROJECT_NAME=FastAPI Bee
VERSION=0.1.0
API_V1_STR=/api/v1

# CORS - Add your frontend URLs
# ALLOWED_ORIGINS=["http://localhost:3000","http://localhost:8000"]

# Database (uncomment when needed)
# DATABASE_URL=sqlite:///./app.db
# DATABASE_URL=postgresql://user:password@localhost/dbname

# Security (uncomment when needed)
# SECRET_KEY=your-secret-key-here-change-in-production
# ALGORITHM=HS256
# ACCESS_TOKEN_EXPIRE_MINUTES=30

# Server
# HOST=0.0.0.0
# PORT=8000
```

### Configuration Management

The application uses **Pydantic Settings** for configuration management:
- Settings are defined in `app/core/config.py`
- Environment variables override default values
- Type validation ensures correct configuration
- `.env` file is loaded automatically

## 🚢 Deployment

### Docker Deployment (Coming Soon)

```dockerfile
# Example Dockerfile structure
FROM python:3.9-slim
WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN pip install poetry && poetry install --no-dev
COPY ./app ./app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Production Considerations

1. **Use environment variables** for sensitive configuration
2. **Set up proper CORS** origins for your frontend
3. **Use HTTPS** in production
4. **Configure logging** for monitoring
5. **Set up database** connection pooling
6. **Use multiple workers** for Uvicorn
7. **Implement rate limiting** for API endpoints
8. **Add authentication/authorization** as needed

## 🤝 Contributing

### Development Workflow

1. **Create a new branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** and ensure code quality:
   ```bash
   poetry run black .
   poetry run flake8 .
   poetry run mypy app/
   ```

3. **Write tests** for your changes:
   ```bash
   # Add tests in appropriate test file
   # Run tests to ensure they pass
   poetry run pytest tests/ -v
   ```

4. **Commit your changes:**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

5. **Push and create a pull request:**
   ```bash
   git push origin feature/your-feature-name
   ```

### Commit Message Convention

Follow conventional commits:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `test:` - Adding or updating tests
- `refactor:` - Code refactoring
- `style:` - Code style changes (formatting)
- `chore:` - Maintenance tasks

## 📚 Additional Resources

### FastAPI Documentation
- [Official FastAPI Docs](https://fastapi.tiangolo.com/)
- [FastAPI Tutorial](https://fastapi.tiangolo.com/tutorial/)
- [Pydantic Documentation](https://docs.pydantic.dev/)

### Learning Resources
- [Python Type Hints](https://docs.python.org/3/library/typing.html)
- [Async/Await in Python](https://docs.python.org/3/library/asyncio.html)
- [Poetry Documentation](https://python-poetry.org/docs/)
- [Pytest Documentation](https://docs.pytest.org/)

## 🐛 Troubleshooting

### Common Issues

**Issue: Poetry not found**
```bash
# Solution: Install poetry
pip install poetry
```

**Issue: Virtual environment not activated**
```bash
# Solution: Activate it
source venv/bin/activate
```

**Issue: Dependencies not installing**
```bash
# Solution: Clear cache and reinstall
poetry cache clear pypi --all
poetry install
```

**Issue: Tests failing**
```bash
# Solution: Ensure virtual environment is activated and dependencies are installed
source venv/bin/activate
poetry install
poetry run pytest tests/ -v
```

**Issue: Port already in use**
```bash
# Solution: Use a different port
poetry run uvicorn app.main:app --reload --port 8001
```

## 📝 Project Status

- ✅ Initial project setup
- ✅ FastAPI application structure
- ✅ Pydantic schemas
- ✅ CRUD endpoints for items
- ✅ Comprehensive test suite (54 tests)
- ✅ API documentation
- ⏳ Database integration (planned)
- ⏳ Authentication/Authorization (planned)
- ⏳ Docker containerization (planned)
- ⏳ CI/CD pipeline (planned)

## 📄 License

MIT License - feel free to use this project for learning or as a template for your own applications.

## 👤 Author

**Hung Truong**
- Email: hungtruongquoc@gmail.com
- GitHub: [@hungtruongquoc](https://github.com/hungtruongquoc)

---

**Built with ❤️ using FastAPI and Python**

