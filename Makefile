# Aicurate - AI Investment Platform
# Makefile for Docker management

.PHONY: help build up down logs shell test clean dev prod

# Default target
help:
	@echo "Aicurate - AI Investment Platform"
	@echo "====================================="
	@echo ""
	@echo "Available commands:"
	@echo "  dev         - Start development environment"
	@echo "  prod        - Start production environment"
	@echo "  build       - Build Docker images"
	@echo "  up          - Start all services"
	@echo "  down        - Stop all services"
	@echo "  logs        - View application logs"
	@echo "  shell       - Open shell in app container"
	@echo "  test        - Run tests in container"
	@echo "  clean       - Clean up containers and images"
	@echo "  restart     - Restart all services"
	@echo "  status      - Show container status"
	@echo ""

# Development environment
dev:
	@echo "Starting development environment..."
	docker-compose -f docker-compose.dev.yml up --build

# Production environment
prod:
	@echo "Starting production environment..."
	docker-compose up --build

# Build images
build:
	@echo "Building Docker images..."
	docker-compose build

# Start services
up:
	@echo "Starting services..."
	docker-compose up -d

# Stop services
down:
	@echo "Stopping services..."
	docker-compose down

# View logs
logs:
	@echo "Viewing application logs..."
	docker-compose logs -f app

# Open shell in container
shell:
	@echo "Opening shell in app container..."
	docker-compose exec app bash

# Run tests
test:
	@echo "Running tests..."
	docker-compose exec app python -m pytest

# Clean up
clean:
	@echo "Cleaning up containers and images..."
	docker-compose down -v
	docker system prune -f
	docker image prune -f

# Restart services
restart:
	@echo "Restarting services..."
	docker-compose restart

# Show status
status:
	@echo "Container status:"
	docker-compose ps

# Scale application
scale:
	@echo "Scaling application to 3 instances..."
	docker-compose up --scale app=3

# Backup logs
backup-logs:
	@echo "Backing up logs..."
	mkdir -p backups
	docker-compose exec app tar -czf /tmp/logs-backup.tar.gz /app/logs
	docker cp $$(docker-compose ps -q app):/tmp/logs-backup.tar.gz ./backups/logs-$$(date +%Y%m%d-%H%M%S).tar.gz

# Update dependencies
update-deps:
	@echo "Updating dependencies..."
	docker-compose exec app pip install --upgrade pip
	docker-compose exec app pip install --upgrade -r requirements.txt

# Database operations (if using external DB)
db-migrate:
	@echo "Running database migrations..."
	docker-compose exec app python -m flask db upgrade

# Security scan
security-scan:
	@echo "Running security scan..."
	docker run --rm -v $(PWD):/app securecodewarrior/docker-security-scan:latest /app

# Performance test
perf-test:
	@echo "Running performance tests..."
	docker run --rm -v $(PWD):/app -w /app loadimpact/k6 run tests/performance.js
