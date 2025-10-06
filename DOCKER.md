# Docker Setup for FastAPI Bee

This document provides instructions for building and running the FastAPI Bee application using Docker.

## Files Overview

- **Dockerfile** - Production-ready multi-stage build
- **Dockerfile.dev** - Development version with hot-reload
- **docker-compose.yml** - Production orchestration
- **docker-compose.dev.yml** - Development orchestration
- **.dockerignore** - Files to exclude from Docker build

## Quick Start

### Production Mode

Build and run the production container:

```bash
# Build the image
docker-compose build

# Start the container
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop the container
docker-compose down
```

The API will be available at:
- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs
- **Health**: http://localhost:8000/health

### Development Mode

Build and run with hot-reload enabled:

```bash
# Build the development image
docker-compose -f docker-compose.dev.yml build

# Start the container
docker-compose -f docker-compose.dev.yml up

# Stop the container
docker-compose -f docker-compose.dev.yml down
```

In development mode:
- Code changes are automatically detected and the server reloads
- Debug logging is enabled
- All dev dependencies are installed

## Docker Commands

### Building Images

```bash
# Build production image
docker build -t fastapi-bee:latest .

# Build development image
docker build -f Dockerfile.dev -t fastapi-bee:dev .

# Build with no cache
docker-compose build --no-cache
```

### Running Containers

```bash
# Run production container
docker run -d -p 8000:8000 --name fastapi-bee fastapi-bee:latest

# Run with environment variables
docker run -d -p 8000:8000 \
  -e ENVIRONMENT=production \
  -e LOG_LEVEL=INFO \
  --name fastapi-bee \
  fastapi-bee:latest

# Run with .env file
docker run -d -p 8000:8000 \
  --env-file .env \
  --name fastapi-bee \
  fastapi-bee:latest

# Run development container with volume mount
docker run -d -p 8000:8000 \
  -v $(pwd)/app:/app/app \
  --name fastapi-bee-dev \
  fastapi-bee:dev
```

### Managing Containers

```bash
# List running containers
docker ps

# View logs
docker logs fastapi-bee
docker logs -f fastapi-bee  # Follow logs

# Execute commands in container
docker exec -it fastapi-bee bash
docker exec fastapi-bee python -c "print('Hello from container')"

# Stop container
docker stop fastapi-bee

# Start container
docker start fastapi-bee

# Remove container
docker rm fastapi-bee

# Remove image
docker rmi fastapi-bee:latest
```

### Docker Compose Commands

```bash
# Start services in background
docker-compose up -d

# Start specific service
docker-compose up -d api

# View logs
docker-compose logs -f
docker-compose logs -f api

# Execute command in service
docker-compose exec api bash
docker-compose exec api python -m pytest

# Restart services
docker-compose restart

# Stop services
docker-compose stop

# Stop and remove containers
docker-compose down

# Stop and remove containers, volumes, and images
docker-compose down -v --rmi all
```

## Environment Variables

Configure the application using environment variables:

### Application Settings
- `PROJECT_NAME` - Project name (default: "FastAPI Bee")
- `VERSION` - API version (default: "0.1.0")
- `API_V1_STR` - API v1 prefix (default: "/api/v1")

### Logging
- `ENVIRONMENT` - Environment mode: `development` or `production`
- `LOG_LEVEL` - Log level: `DEBUG`, `INFO`, `WARNING`, `ERROR`

### CORS
- `ALLOWED_ORIGINS` - JSON array of allowed origins

### Example .env file

```env
PROJECT_NAME=FastAPI Bee
VERSION=0.1.0
API_V1_STR=/api/v1
ENVIRONMENT=production
LOG_LEVEL=INFO
ALLOWED_ORIGINS=["http://localhost:3000","https://example.com"]
```

## Multi-Stage Build

The production Dockerfile uses a multi-stage build for optimal image size:

1. **Builder Stage**: Installs Poetry and dependencies
2. **Runtime Stage**: Copies only necessary files and virtual environment

Benefits:
- Smaller final image size
- Faster deployment
- Improved security (no build tools in production)

## Security Features

- **Non-root user**: Application runs as `appuser` (not root)
- **Minimal base image**: Uses `python:3.9-slim` for smaller attack surface
- **Health checks**: Built-in health check endpoint monitoring
- **No dev dependencies**: Production image excludes development packages

## Health Checks

The container includes a health check that:
- Runs every 30 seconds
- Checks the `/health` endpoint
- Marks container as unhealthy after 3 failed attempts
- Useful for orchestration tools (Kubernetes, Docker Swarm)

```bash
# Check container health status
docker inspect --format='{{.State.Health.Status}}' fastapi-bee
```

## Troubleshooting

### Container won't start

```bash
# Check logs
docker-compose logs api

# Check if port is already in use
lsof -i :8000

# Rebuild without cache
docker-compose build --no-cache
```

### Permission issues

```bash
# Ensure files are readable
chmod -R 755 app/

# Check container user
docker-compose exec api whoami
```

### Hot-reload not working in development

```bash
# Ensure volumes are mounted correctly
docker-compose -f docker-compose.dev.yml config

# Restart the container
docker-compose -f docker-compose.dev.yml restart
```

### Image size too large

```bash
# Check image size
docker images fastapi-bee

# Use multi-stage build (production Dockerfile)
# Remove unnecessary files via .dockerignore
```

## Production Deployment

### Using Docker Compose

```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose up -d --build

# Check status
docker-compose ps
```

### Using Docker Swarm

```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml fastapi-bee

# List services
docker service ls

# Scale service
docker service scale fastapi-bee_api=3
```

### Using Kubernetes

Convert docker-compose.yml to Kubernetes manifests:

```bash
# Install kompose
curl -L https://github.com/kubernetes/kompose/releases/download/v1.31.2/kompose-linux-amd64 -o kompose
chmod +x kompose
sudo mv kompose /usr/local/bin/

# Convert to Kubernetes
kompose convert -f docker-compose.yml

# Apply to cluster
kubectl apply -f .
```

## Best Practices

1. **Use .dockerignore**: Exclude unnecessary files from build context
2. **Multi-stage builds**: Keep production images small
3. **Non-root user**: Run containers as non-root for security
4. **Health checks**: Always include health check endpoints
5. **Environment variables**: Use env vars for configuration
6. **Volume mounts**: Use volumes for persistent data
7. **Logging**: Configure structured logging for production
8. **Resource limits**: Set memory and CPU limits in production

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [Poetry in Docker](https://python-poetry.org/docs/faq/#poetry-busts-my-docker-cache)

