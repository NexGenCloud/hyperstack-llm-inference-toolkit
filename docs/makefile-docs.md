# Makefile Documentation

This document provides a brief overview of the Makefile commands available in the project.

## Basic Commands

Below are the basic commands that can be used to build, run, and stop the application.

```bash
# Build and start app services containers in attached mode
make dev-up

# Build and start app services containers in detached mode
make dev-daemon

# Check services container logs
make dev-logs

# SSH into app container for troubleshoot
make dev-ssh

# Apply database migrations
❯ make dev-migrate
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.env] No changes in schema detected.
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.

# Stop all services containers
make dev-stop

# Please check other useful make targets by:
❯ make help
  dev-build                          Build all services
  dev-up                             Start all services in attached mode
  dev-daemon                         Start all services in detached mode
  dev-ssh                            SSH into backend app
  dev-migrate                        Apply database migrations
  dev-test                           Run pytest unit tests
  dev-stop                           Stop all services
  dev-down                           Stop and remove all services
  dev-restart                        Restart all services
  dev-logs                           View logs
  dev-clean                          Clean up all containers, networks, images, and orphans
  dev-clean-volumes                  Clean up volumes
  dev-foreground                     Start all services in foreground mode
```

## Unit Tests (PyTest)

Unit tests are written with PyTest. These unit tests will run on a dedicated database (i.e. `inference_test_db`) inside postgres container. We set it up during the development setup, you will notice the following lines in postgres container logs:

```bash
llm_binding.db   | Multiple database creation requested: inference_db, inference_test_db
llm_binding.db   |   Creating database 'inference_db' and granting privileges to 'devuser'
llm_binding.db   | CREATE DATABASE
llm_binding.db   | GRANT
llm_binding.db   |   Creating database 'inference_test_db' and granting privileges to 'devuser'
llm_binding.db   | CREATE DATABASE
llm_binding.db   | GRANT
llm_binding.db   | Multiple databases created
```

An important part of tests runner boilerplate is `db_session` fixture which is designed to provide a clean and isolated database environment for each test function. It ensures that changes made to the database during a test are rolled back and that the database is returned to a pristine state for the next test. The fixture is set to be auto-reused even if not specified explicitly.

In order to run unit tests, please follow:

```bash
# Run all unit tests
make dev-test

# Useful while developing unit tests OR during TDD:

# ssh into web container
$ make dev-ssh

# Run all tests after make `dev-ssh`
APP_SETTINGS=config.TestConfig pytest tests/ -vv

# Run a tests in a class group
APP_SETTINGS=config.TestConfig pytest tests/test_apis.py::TestGenerateAPIKeyEndpoint::test_generate_api_key_success -vv

# Run a single test
APP_SETTINGS=config.TestConfig pytest tests/test_apis.py::TestGenerateAPIKeyEndpoint::test_generate_api_key_success -vv
```

## Integration Tests (PyTest)

Integration tests are written with pytest. These test will run on our actual flask application during runtime.
The MISTRAL model (mistralai/Mistral-7B-Instruct-v0.2) should be added to the app using UI (other models can be added
as well but need to be added to model enum in the integration tests if we want to make that work).
Name and the Endpoint URL of the model should be set up before running the integration tests.

You can use the UI to deploy the model. The Docker run command to deploy the MISRAL model is as follows. Please note: this model requires gated access (see instructions [here](https://huggingface.co/docs/transformers.js/en/guides/private))

```
export HF_TOKEN="[replace-token-with-gated-access]"
mkdir -p /home/ubuntu/data/hf
docker run -d --gpus all \
    -e HF_TOKEN="$HF_TOKEN" \
    -v /home/ubuntu/data/hf:/root/.cache/huggingface \
    -p 8000:8000 \
    --ipc=host --restart always \
    vllm/vllm-openai:latest --model \
    "mistralai/Mistral-7B-Instruct-v0.2" \
    --gpu-memory-utilization 0.9 --max-model-len 15360 \
    --chat-template examples/tool_chat_template_mistral.jinja
```

```bash
# Run all Integration test
make dev-integration-test
```

# Deployment

You can build and up production environment quickly using following commands:

NOTE: production environment will not have dev database to run tests, so tests
should only be running in DEV environment.

## Initial Deployment

For initially deploying the flask app we can use following command:

```bash
make deploy-app
```

This will deploy an flask app in hyperstack Virtual machine, please make sure required credentials are added in backend/deployment/conf/build.manifest.yaml file.

The following commands can be used to build up the app again.

```bash
make prod-build

make prod-up
```

# Database Backup/Restore

Database backups are done automatically every 6 hours (by default, this is configurable in the environment) and are pushed to s3 bucket in a background task using celery beat.

To restore database to a specific point using dump file we have a separate command

```bash
make restore-dev-database FILE=<backup-file-name> # for dev
make restore-prod-database FILE=<backup-file-name> # for prod
```

NOTE: Make sure you have s3 credentials specified in the environment(.env) file
