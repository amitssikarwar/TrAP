# TrendsQL-KG Makefile
.PHONY: help setup install test run clean docker-up docker-down docker-build docker-logs

# Default target
help:
	@echo "TrendsQL-KG - Knowledge Graph + Agentic RAG for Trend Analysis"
	@echo ""
	@echo "Available commands:"
	@echo "  setup          - Initial setup (install dependencies, setup environment)"
	@echo "  install        - Install Python dependencies"
	@echo "  test           - Run tests"
	@echo "  run            - Run the application locally"
	@echo "  docker-up      - Start all services with Docker Compose"
	@echo "  docker-down    - Stop all services"
	@echo "  docker-build   - Build Docker images"
	@echo "  docker-logs    - Show Docker logs"
	@echo "  clean          - Clean up temporary files"
	@echo "  db-up          - Start only database services"
	@echo "  api            - Start the API service"
	@echo "  ingest-exp     - Run exploding topics ingestion"
	@echo "  ingest-gt      - Run Google Trends ingestion"
	@echo "  kg-build       - Build/refresh knowledge graph"

# Setup environment
setup: install
	@echo "Setting up TrendsQL-KG..."
	@if [ ! -f .env ]; then \
		echo "Creating .env file from template..."; \
		cp env.example .env; \
		echo "Please edit .env file with your configuration"; \
	fi
	@echo "Setup complete! Edit .env file with your API keys and configuration."

# Install dependencies
install:
	@echo "Installing Python dependencies..."
	pip install -r requirements.txt

# Run tests
test:
	@echo "Running tests..."
	python -m pytest tests/ -v

# Run application locally
run:
	@echo "Starting TrendsQL-KG application..."
	uvicorn app.app:app --reload --host 0.0.0.0 --port 8000

# Docker commands
docker-up:
	@echo "Starting all services with Docker Compose..."
	docker-compose up -d

docker-down:
	@echo "Stopping all services..."
	docker-compose down

docker-build:
	@echo "Building Docker images..."
	docker-compose build

docker-logs:
	@echo "Showing Docker logs..."
	docker-compose logs -f

# Database only
db-up:
	@echo "Starting database services..."
	docker-compose up -d postgres neo4j

# API service
api:
	@echo "Starting API service..."
	docker-compose up -d app

# Data ingestion commands
ingest-exp:
	@echo "Running exploding topics ingestion..."
	python -m ingestors.run_ingest exploding --config config/exploding.yml

ingest-gt:
	@echo "Running Google Trends ingestion..."
	python -m ingestors.run_ingest google --config config/google_trends.yml

# Knowledge Graph commands
kg-build:
	@echo "Building knowledge graph..."
	python -m ingestors.run_build_kg --config config/kg.yml

# Development commands
dev-setup: setup
	@echo "Setting up development environment..."
	@echo "Installing development dependencies..."
	pip install -r requirements-dev.txt || echo "No requirements-dev.txt found"
	@echo "Development setup complete!"

dev-run:
	@echo "Running in development mode..."
	uvicorn app.app:app --reload --host 0.0.0.0 --port 8000 --log-level debug

# Cleanup
clean:
	@echo "Cleaning up..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov

# Database management
db-reset:
	@echo "Resetting database..."
	docker-compose down -v
	docker-compose up -d postgres neo4j
	@echo "Waiting for databases to be ready..."
	sleep 10
	@echo "Database reset complete!"

db-migrate:
	@echo "Running database migrations..."
	# TODO: Add migration commands when implemented

# Health checks
health:
	@echo "Checking service health..."
	curl -f http://localhost:8000/health || echo "API not responding"
	curl -f http://localhost:5432 || echo "PostgreSQL not responding"
	curl -f http://localhost:7474 || echo "Neo4j not responding"

# Logs
logs-api:
	@echo "API logs:"
	docker-compose logs -f app

logs-db:
	@echo "Database logs:"
	docker-compose logs -f postgres

logs-neo4j:
	@echo "Neo4j logs:"
	docker-compose logs -f neo4j

# Backup and restore
backup:
	@echo "Creating database backup..."
	docker-compose exec postgres pg_dump -U postgres trendsql_kg > backup_$(shell date +%Y%m%d_%H%M%S).sql

restore:
	@echo "Restoring database from backup..."
	@read -p "Enter backup file name: " backup_file; \
	docker-compose exec -T postgres psql -U postgres trendsql_kg < $$backup_file

# Production commands
prod-build:
	@echo "Building production image..."
	docker build -t trendsql-kg:latest .

prod-run:
	@echo "Running production container..."
	docker run -d --name trendsql-kg-prod \
		-p 8000:8000 \
		--env-file .env \
		trendsql-kg:latest

# Monitoring
monitor:
	@echo "System monitoring:"
	@echo "CPU and Memory usage:"
	docker stats --no-stream
	@echo ""
	@echo "Container status:"
	docker-compose ps

# Documentation
docs:
	@echo "Generating documentation..."
	# TODO: Add documentation generation commands

# Linting and formatting
lint:
	@echo "Running linter..."
	flake8 app/ tests/
	black --check app/ tests/

format:
	@echo "Formatting code..."
	black app/ tests/
	isort app/ tests/

# Security
security-check:
	@echo "Running security checks..."
	bandit -r app/
	safety check

# Performance
benchmark:
	@echo "Running performance benchmarks..."
	# TODO: Add benchmark commands

# Quick start
quick-start: setup db-up
	@echo "Waiting for databases to be ready..."
	sleep 15
	@echo "Starting API..."
	make api
	@echo "TrendsQL-KG is ready!"
	@echo "API: http://localhost:8000"
	@echo "Docs: http://localhost:8000/docs"
	@echo "Neo4j Browser: http://localhost:7474"
