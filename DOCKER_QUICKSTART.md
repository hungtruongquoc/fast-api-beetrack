# Docker Quick Start Guide

Get FastAPI Bee running in Docker in under 2 minutes!

## Prerequisites

- Docker installed ([Get Docker](https://docs.docker.com/get-docker/))
- Docker Compose installed (usually comes with Docker Desktop)

## 🚀 Quick Start

### Option 1: Production Mode (Recommended for Testing)

```bash
# 1. Build the image
docker-compose build

# 2. Start the container
docker-compose up -d

# 3. Check if it's running
curl http://localhost:8000/health

# 4. View API docs
open http://localhost:8000/docs
```

### Option 2: Development Mode (Hot-Reload)

```bash
# 1. Build the development image
docker-compose -f docker-compose.dev.yml build

# 2. Start the container (with logs)
docker-compose -f docker-compose.dev.yml up

# 3. Make changes to code - server auto-reloads!
```

### Option 3: Using the Docker Script (Easiest)

```bash
# Production
./scripts/docker.sh build
./scripts/docker.sh up
./scripts/docker.sh logs

# Development
./scripts/docker.sh dev-build
./scripts/docker.sh dev-up
```

## 📋 Common Commands

### Production Commands

```bash
# Start containers
docker-compose up -d

# View logs
docker-compose logs -f

# Stop containers
docker-compose down

# Restart containers
docker-compose restart

# Check status
docker-compose ps
```

### Development Commands

```bash
# Start with hot-reload
docker-compose -f docker-compose.dev.yml up

# Stop
docker-compose -f docker-compose.dev.yml down

# View logs
docker-compose -f docker-compose.dev.yml logs -f
```

### Management Commands

```bash
# Open shell in container
docker-compose exec api bash

# Run tests in container
docker-compose exec api poetry run pytest

# Check health
curl http://localhost:8000/health

# View container details
docker inspect fastapi-bee
```

## 🔧 Configuration

### Environment Variables

Edit `docker-compose.yml` to customize:

```yaml
environment:
  - PROJECT_NAME=FastAPI Bee
  - VERSION=0.1.0
  - ENVIRONMENT=production
  - LOG_LEVEL=INFO
```

Or use a `.env` file:

```bash
# Uncomment in docker-compose.yml:
env_file:
  - .env
```

### Port Configuration

Change the port mapping in `docker-compose.yml`:

```yaml
ports:
  - "3000:8000"  # Access on port 3000 instead of 8000
```

## 🧪 Testing

### Run Tests in Container

```bash
# Using docker-compose
docker-compose exec api poetry run pytest tests/ -v

# Using the script
./scripts/docker.sh test
```

### Run Specific Tests

```bash
docker-compose exec api poetry run pytest tests/test_main.py -v
```

## 🐛 Troubleshooting

### Container won't start

```bash
# Check logs
docker-compose logs api

# Rebuild without cache
docker-compose build --no-cache
```

### Port already in use

```bash
# Check what's using port 8000
lsof -i :8000

# Or change port in docker-compose.yml
ports:
  - "8001:8000"
```

### Permission issues

```bash
# Ensure files are readable
chmod -R 755 app/

# Rebuild
docker-compose build
```

### Can't connect to container

```bash
# Check if container is running
docker ps

# Check container health
docker inspect --format='{{.State.Health.Status}}' fastapi-bee

# Check logs
docker-compose logs -f api
```

## 🧹 Cleanup

### Remove containers and images

```bash
# Stop and remove containers
docker-compose down

# Remove containers and volumes
docker-compose down -v

# Remove images
docker rmi fastapi-bee:latest

# Or use the script
./scripts/docker.sh clean
```

### Clean up Docker system

```bash
# Remove unused containers, networks, images
docker system prune -f

# Remove everything including volumes
docker system prune -a --volumes
```

## 📚 Next Steps

- **Full Documentation**: See [DOCKER.md](DOCKER.md) for comprehensive guide
- **API Documentation**: Visit http://localhost:8000/docs
- **Main README**: See [README.md](README.md) for project overview

## 🎯 Quick Reference

| Command | Description |
|---------|-------------|
| `docker-compose up -d` | Start production containers |
| `docker-compose down` | Stop containers |
| `docker-compose logs -f` | View logs |
| `docker-compose exec api bash` | Open shell |
| `./scripts/docker.sh help` | Show all Docker commands |

## 🔗 Useful URLs

Once running:

- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health**: http://localhost:8000/health
- **OpenAPI**: http://localhost:8000/api/v1/openapi.json

## 💡 Tips

1. **Use development mode** when coding - changes auto-reload
2. **Use production mode** for testing deployment
3. **Check logs** if something doesn't work
4. **Use the script** (`./scripts/docker.sh`) for convenience
5. **Read DOCKER.md** for advanced usage

---

**Need help?** Check [DOCKER.md](DOCKER.md) for detailed documentation.

