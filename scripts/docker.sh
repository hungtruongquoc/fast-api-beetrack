#!/bin/bash

# FastAPI Bee - Docker Management Script
# Convenient commands for Docker operations

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

# Function to check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        print_info "Install Docker from: https://docs.docker.com/get-docker/"
        exit 1
    fi
    print_success "Docker is installed: $(docker --version)"
}

# Function to check if Docker Compose is installed
check_docker_compose() {
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed"
        print_info "Install Docker Compose from: https://docs.docker.com/compose/install/"
        exit 1
    fi
    print_success "Docker Compose is installed: $(docker-compose --version)"
}

# Function to show usage
show_usage() {
    cat << EOF
${CYAN}FastAPI Bee - Docker Management Script${NC}

${YELLOW}Usage:${NC}
  ./scripts/docker.sh [command]

${YELLOW}Production Commands:${NC}
  ${GREEN}build${NC}            Build production Docker image
  ${GREEN}up${NC}               Start production containers
  ${GREEN}down${NC}             Stop and remove production containers
  ${GREEN}restart${NC}          Restart production containers
  ${GREEN}logs${NC}             View production container logs
  ${GREEN}status${NC}           Show production container status

${YELLOW}Development Commands:${NC}
  ${GREEN}dev-build${NC}        Build development Docker image
  ${GREEN}dev-up${NC}           Start development containers with hot-reload
  ${GREEN}dev-down${NC}         Stop and remove development containers
  ${GREEN}dev-restart${NC}      Restart development containers
  ${GREEN}dev-logs${NC}         View development container logs
  ${GREEN}dev-shell${NC}        Open shell in development container

${YELLOW}Management Commands:${NC}
  ${GREEN}exec${NC}             Execute command in running container
  ${GREEN}shell${NC}            Open bash shell in production container
  ${GREEN}test${NC}             Run tests in container
  ${GREEN}clean${NC}            Remove all containers and images
  ${GREEN}prune${NC}            Clean up Docker system
  ${GREEN}health${NC}           Check container health status

${YELLOW}Image Commands:${NC}
  ${GREEN}images${NC}           List Docker images
  ${GREEN}ps${NC}               List running containers
  ${GREEN}inspect${NC}          Inspect container details

${YELLOW}Examples:${NC}
  ./scripts/docker.sh build         # Build production image
  ./scripts/docker.sh dev-up        # Start development with hot-reload
  ./scripts/docker.sh logs          # View logs
  ./scripts/docker.sh exec pytest   # Run tests in container

EOF
}

# Production commands
docker_build() {
    print_header "Building Production Docker Image"
    check_docker
    check_docker_compose
    docker-compose build
    print_success "Production image built successfully!"
}

docker_up() {
    print_header "Starting Production Containers"
    check_docker
    check_docker_compose
    docker-compose up -d
    print_success "Production containers started!"
    print_info "API available at: http://localhost:8000"
    print_info "Docs available at: http://localhost:8000/docs"
}

docker_down() {
    print_header "Stopping Production Containers"
    check_docker
    check_docker_compose
    docker-compose down
    print_success "Production containers stopped!"
}

docker_restart() {
    print_header "Restarting Production Containers"
    check_docker
    check_docker_compose
    docker-compose restart
    print_success "Production containers restarted!"
}

docker_logs() {
    print_header "Production Container Logs"
    check_docker
    check_docker_compose
    docker-compose logs -f
}

docker_status() {
    print_header "Production Container Status"
    check_docker
    check_docker_compose
    docker-compose ps
}

# Development commands
docker_dev_build() {
    print_header "Building Development Docker Image"
    check_docker
    check_docker_compose
    docker-compose -f docker-compose.dev.yml build
    print_success "Development image built successfully!"
}

docker_dev_up() {
    print_header "Starting Development Containers"
    check_docker
    check_docker_compose
    print_info "Starting with hot-reload enabled..."
    docker-compose -f docker-compose.dev.yml up
}

docker_dev_down() {
    print_header "Stopping Development Containers"
    check_docker
    check_docker_compose
    docker-compose -f docker-compose.dev.yml down
    print_success "Development containers stopped!"
}

docker_dev_restart() {
    print_header "Restarting Development Containers"
    check_docker
    check_docker_compose
    docker-compose -f docker-compose.dev.yml restart
    print_success "Development containers restarted!"
}

docker_dev_logs() {
    print_header "Development Container Logs"
    check_docker
    check_docker_compose
    docker-compose -f docker-compose.dev.yml logs -f
}

docker_dev_shell() {
    print_header "Opening Shell in Development Container"
    check_docker
    check_docker_compose
    docker-compose -f docker-compose.dev.yml exec api bash
}

# Management commands
docker_exec() {
    print_header "Executing Command in Container"
    check_docker
    check_docker_compose
    local cmd="${@:2}"
    if [[ -z "$cmd" ]]; then
        print_error "No command specified"
        print_info "Usage: ./scripts/docker.sh exec <command>"
        exit 1
    fi
    docker-compose exec api $cmd
}

docker_shell() {
    print_header "Opening Shell in Production Container"
    check_docker
    check_docker_compose
    docker-compose exec api bash
}

docker_test() {
    print_header "Running Tests in Container"
    check_docker
    check_docker_compose
    docker-compose exec api poetry run pytest tests/ -v
}

docker_clean() {
    print_header "Cleaning Docker Resources"
    check_docker
    check_docker_compose
    
    print_warning "This will remove all FastAPI Bee containers and images"
    read -p "Are you sure? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Stopping and removing containers..."
        docker-compose down -v 2>/dev/null || true
        docker-compose -f docker-compose.dev.yml down -v 2>/dev/null || true
        
        print_info "Removing images..."
        docker rmi fastapi-bee:latest 2>/dev/null || true
        docker rmi fastapi-bee:dev 2>/dev/null || true
        docker rmi fastapi-bee-api:latest 2>/dev/null || true
        
        print_success "Cleanup completed!"
    else
        print_info "Cleanup cancelled"
    fi
}

docker_prune() {
    print_header "Pruning Docker System"
    check_docker
    
    print_warning "This will remove unused Docker resources"
    docker system prune -f
    print_success "Docker system pruned!"
}

docker_health() {
    print_header "Checking Container Health"
    check_docker
    
    local container_name="fastapi-bee"
    if docker ps --format '{{.Names}}' | grep -q "^${container_name}$"; then
        local health=$(docker inspect --format='{{.State.Health.Status}}' $container_name 2>/dev/null || echo "no healthcheck")
        print_info "Container: $container_name"
        print_info "Health Status: $health"
        
        if [[ "$health" == "healthy" ]]; then
            print_success "Container is healthy!"
        elif [[ "$health" == "no healthcheck" ]]; then
            print_warning "No health check configured"
        else
            print_error "Container is unhealthy!"
        fi
    else
        print_error "Container '$container_name' is not running"
    fi
}

# Image commands
docker_images() {
    print_header "Docker Images"
    check_docker
    docker images | grep -E "fastapi-bee|REPOSITORY"
}

docker_ps() {
    print_header "Running Containers"
    check_docker
    docker ps -a | grep -E "fastapi-bee|CONTAINER"
}

docker_inspect() {
    print_header "Container Inspection"
    check_docker
    docker inspect fastapi-bee 2>/dev/null || print_error "Container 'fastapi-bee' not found"
}

# Main script logic
main() {
    local command=${1:-help}
    
    case "$command" in
        build)
            docker_build
            ;;
        up)
            docker_up
            ;;
        down)
            docker_down
            ;;
        restart)
            docker_restart
            ;;
        logs)
            docker_logs
            ;;
        status)
            docker_status
            ;;
        dev-build)
            docker_dev_build
            ;;
        dev-up)
            docker_dev_up
            ;;
        dev-down)
            docker_dev_down
            ;;
        dev-restart)
            docker_dev_restart
            ;;
        dev-logs)
            docker_dev_logs
            ;;
        dev-shell)
            docker_dev_shell
            ;;
        exec)
            docker_exec "$@"
            ;;
        shell)
            docker_shell
            ;;
        test)
            docker_test
            ;;
        clean)
            docker_clean
            ;;
        prune)
            docker_prune
            ;;
        health)
            docker_health
            ;;
        images)
            docker_images
            ;;
        ps)
            docker_ps
            ;;
        inspect)
            docker_inspect
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

