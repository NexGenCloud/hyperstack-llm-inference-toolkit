# Define variables
DEV_COMPOSE_FILE_OPTIONS=-f docker-compose.base.yml -f docker-compose.dev.yml
PROD_COMPOSE_FILE_OPTIONS=-f docker-compose.base.yml -f docker-compose.prod.yml

# Define targets
.PHONY: all build up down restart logs clean clean-volumes clean-restart foreground

help:
	@egrep -h '\s##\s' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m  %-30s\033[0m %s\n", $$1, $$2}'

# Development targets

dev-build: ## Build all services
	@docker compose $(DEV_COMPOSE_FILE_OPTIONS) build

dev-up: ## Start all services in detached mode
	@docker compose $(DEV_COMPOSE_FILE_OPTIONS) up --build

dev-ssh: ## SSH into backend app
	@docker compose $(DEV_COMPOSE_FILE_OPTIONS) exec app /bin/bash

dev-migrate: ## Apply database migrations
	@docker compose $(DEV_COMPOSE_FILE_OPTIONS) exec app /bin/bash -c "flask db migrate && flask db upgrade"

dev-test: ## Run pytest unit tests
	@docker compose $(DEV_COMPOSE_FILE_OPTIONS) exec app /bin/bash -c "bash scripts/run_tests.sh"

dev-integration-test: ## Run pytest integration tests
	@docker compose $(DEV_COMPOSE_FILE_OPTIONS) exec app /bin/bash -c "bash scripts/run_int_tests.sh"

dev-stop: ## Stop all services
	@docker compose $(DEV_COMPOSE_FILE_OPTIONS) stop

dev-down: ## Stop and remove all services
	@docker compose $(DEV_COMPOSE_FILE_OPTIONS) down

# Add start/stop

dev-restart: dev-stop dev-up ## Restart all services

dev-logs: ## View logs
	@docker compose $(DEV_COMPOSE_FILE_OPTIONS) logs -f

dev-clean: ## Clean up all containers, networks, images, and orphans
	@docker compose $(DEV_COMPOSE_FILE_OPTIONS) down -v --rmi all --remove-orphans

dev-clean-volumes: ## Clean up volumes
	@docker volume prune -f

# Clean, build, and restart everything
dev-clean-restart: dev-clean dev-build up
	@echo "Application has been cleaned, built, and restarted."

dev-foreground: dev-build ## Start all services in foreground mode
	@docker compose $(DEV_COMPOSE_FILE_OPTIONS) up

dev-daemon:
	@docker compose $(DEV_COMPOSE_FILE_OPTIONS) up -d

# Production targets

prod-build: ## Build all services
	@docker compose $(PROD_COMPOSE_FILE_OPTIONS) build

prod-up: ## Start all services in detached mode
	@docker compose $(PROD_COMPOSE_FILE_OPTIONS) up --build

prod-ssh: ## SSH into backend app
	@docker compose $(PROD_COMPOSE_FILE_OPTIONS) exec app /bin/bash

prod-migrate: ## Apply database migrations
	@docker compose $(PROD_COMPOSE_FILE_OPTIONS) exec app /bin/bash -c "flask db upgrade"

prod-logs: ## View logs
	@docker compose $(PROD_COMPOSE_FILE_OPTIONS) logs -f

prod-stop: ## Stop all services
	@docker compose $(PROD_COMPOSE_FILE_OPTIONS) stop

prod-down: ## Stop and remove all services
	@docker compose $(PROD_COMPOSE_FILE_OPTIONS) down

prod-daemon:
	@docker compose $(PROD_COMPOSE_FILE_OPTIONS) up -d
prod-clean:
	@docker compose $(PROD_COMPOSE_FILE_OPTIONS) down -v --rmi all --remove-orphans

deploy-app: # deploy flask app
	$(eval ENV_FILE := .env)
	@echo " - setup env $(ENV_FILE)"
	$(eval include .env)
	$(eval export sed 's/=.*//' .env)
	cd deployment \
		&& docker build -t deploy-flask . > /dev/null \
		&& docker run -it --rm \
		--env ADMIN_API_KEY=$(ADMIN_API_KEY) \
		deploy-flask

restore-dev-database: # restore db backup (FILE=dump-file)
	$(eval ENV_FILE := .env)
	@echo " - setup env $(ENV_FILE)"
	$(eval include .env)
	$(eval export sed 's/=.*//' .env)
	docker compose $(DEV_COMPOSE_FILE_OPTIONS) down app; \
	cd deployment; \
	docker build -t restore-db . > /dev/null; \
	docker run -it --rm \
		--network inference_network \
		--env MYSQL_DB_HOST=$(MYSQL_DB_HOST) \
		--env MYSQL_ROOT_PASSWORD=$(MYSQL_ROOT_PASSWORD) \
		--env MYSQL_DATABASE=$(MYSQL_DATABASE) \
		--env S3_ENDPOINT_URL=$(S3_ENDPOINT_URL) \
		--env S3_ACCESS_KEY=$(S3_ACCESS_KEY) \
		--env S3_SECRET_KEY=$(S3_SECRET_KEY) \
		--env S3_BUCKET_NAME=$(S3_BUCKET_NAME) \
		restore-db python /app/scripts/restore_database.py \
		--file ${FILE}; \
	cd .. && docker compose $(DEV_COMPOSE_FILE_OPTIONS) up -d app;

restore-prod-database: # restore db backup (FILE=dump-file)
	$(eval ENV_FILE := .env)
	@echo " - setup env $(ENV_FILE)"
	$(eval include .env)
	$(eval export sed 's/=.*//' .env)
	docker compose $(PROD_COMPOSE_FILE_OPTIONS) down app; \
	cd deployment; \
	docker build -t restore-db . > /dev/null; \
	docker run -it --rm \
		--network inference_network \
		--env MYSQL_DB_HOST=$(MYSQL_DB_HOST) \
		--env MYSQL_ROOT_PASSWORD=$(MYSQL_ROOT_PASSWORD) \
		--env MYSQL_DATABASE=$(MYSQL_DATABASE) \
		--env S3_ENDPOINT_URL=$(S3_ENDPOINT_URL) \
		--env S3_ACCESS_KEY=$(S3_ACCESS_KEY) \
		--env S3_SECRET_KEY=$(S3_SECRET_KEY) \
		--env S3_BUCKET_NAME=$(S3_BUCKET_NAME) \
		restore-db python /app/scripts/restore_database.py \
		--file ${FILE}; \
	cd .. && docker compose $(PROD_COMPOSE_FILE_OPTIONS) up -d app;
