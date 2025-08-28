.PHONY: help install dev test clean db-up db-down db-init run ingest-exploding ingest-google docker-build docker-up docker-down

help: ## Show this help message
	@echo "TrendSQL - Text-to-SQL API for trend data analysis"
	@echo ""
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install Python dependencies
	pip install -r requirements.txt

dev: ## Install development dependencies
	pip install -r requirements.txt
	pip install pytest pytest-asyncio

test: ## Run tests
	python -m pytest tests/ -v

clean: ## Clean up temporary files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +

db-up: ## Start PostgreSQL database with Docker
	docker run -d --name trendsql-db \
		-e POSTGRES_DB=trendsql \
		-e POSTGRES_USER=postgres \
		-e POSTGRES_PASSWORD=postgres \
		-p 5432:5432 \
		postgres:16

db-down: ## Stop PostgreSQL database
	docker stop trendsql-db || true
	docker rm trendsql-db || true

db-init: ## Initialize database schema
	psql -h localhost -U postgres -d trendsql -f db/schema.sql
	psql -h localhost -U postgres -d trendsql -f db/seed.sql

run: ## Run the FastAPI application locally
	uvicorn app.app:app --reload --host 0.0.0.0 --port 8000

ingest-exploding: ## Ingest exploding topics data
	python -m ingestors.run_ingest exploding --config config/exploding.yml

ingest-google: ## Ingest Google Trends data
	python -m ingestors.run_ingest google --config config/google_trends.yml

docker-build: ## Build Docker image
	docker build -t trendsql .

docker-up: ## Start services with Docker Compose
	docker-compose up -d

docker-down: ## Stop Docker Compose services
	docker-compose down

docker-logs: ## View Docker Compose logs
	docker-compose logs -f

setup: ## Complete setup (install, db-up, db-init)
	$(MAKE) install
	$(MAKE) db-up
	sleep 5
	$(MAKE) db-init

reset: ## Reset everything (clean, db-down, db-up, db-init)
	$(MAKE) clean
	$(MAKE) db-down
	$(MAKE) db-up
	sleep 5
	$(MAKE) db-init
