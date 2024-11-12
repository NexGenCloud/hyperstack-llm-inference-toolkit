# Architecture - Hyperstack LLM Inference Toolkit

## Introduction

This document serves as a comprehensive user guide for the Hyperstack LLM Inference Toolkit, an open-source tool that simplifies Large Language Model (LLM) management and deployment using Hyperstack.

## Basic architecture

The Hyperstack LLM Inference Toolkit allows you to deploy, manage, and prototype LLM models with ease.

![Architecture](./images/basic-architecture.png)

The basic architecture consists of:

### 1. Proxy API VM:

- **Description**: This VM acts as a proxy API that forwards requests to your LLM models. It also provides a user-friendly interface for interacting with the toolkit.
- **User interfaces**: The UI consists of the following:
  1.  **🏠 Home**: Home page describing the toolkit
  2.  **📦 Models**: View all deployed LLMs, add new models, and manage replicas for each model
  3.  **👩‍💻 Playground**: Interact with your deployed LLM models
  4.  **🔑 API Keys**: Create and manage API keys for your users
  5.  **📊 Monitoring**: View and interact with the data stored in your databases
- **API endpoints**: The API endpoints include (for more details, please check out [API endpoint documentation](./api-endpoints.md)):
  1. `/chat/completions`: Chat completions API compatible with [OpenAI API standards](https://platform.openai.com/docs/api-reference/chat).
  2. `/generate_api_key`: Generates API keys for accessing the inference API.
  3. `/delete_api_key`: Deletes or disables an API key.
  4. `/tables`: Lists available database tables in the toolkit.
  5. `/tables/<string:table_name>`: Retrieves data from a specific database table (up to 100 rows).
  6. `/models`: Lists all models, with an option to filter for active models.
  7. `/models/<string:model_name>`: Fetches details of a specific model.
  8. `/models` (POST): Creates a new LLM model.
  9. `/models/<int:model_id>` (DELETE): Deletes a specific model and its replicas.
  10. `/models/<int:model_id>/replicas`: Retrieves all replicas for a specified model.
  11. `/models/<int:model_id>/replicas` (POST): Creates a new replica for a specified model.
  12. `/models/replicas/<int:replica_id>` (PUT): Updates a specific replica’s configuration.
  13. `/replicas/<int:replica_id>` (DELETE): Deletes a specific replica and its security rules.
- Database tables: The toolkit uses the following database tables:
  1. `api_keys`: Stores API keys for accessing the inference API.
  2. `llm_models`: Stores information about LLM models.
  3. `metrics`: Stores usage metrics for the inference API.
  4. `replicas`: Stores information about model replicas (deployed instances of an LLM model with specific configuration and endpoint details).
  5. `replica_security_rules`: Stores security rules for model replicas.

### 2. Inference Engine VMs:

- **Description**: These VMs host the LLM models and handle inference requests from the proxy API VM.
- **Models**: The toolkit comes pre-configured with two LLM models:
  1. **NousResearch/Meta-Llama-3.1-8B**
  2. **microsoft/Phi-3-medium-128k-instruct**
- **Technology**: The Inference Engine VMs use [vLLM](https://docs.vllm.ai/en/latest/) to host the LLM models.
- **API endpoints**: To see which API endpoints are available for each model, refer to [vLLM API documentation](https://docs.vllm.ai/en/v0.6.0/serving/openai_compatible_server.html).

Please note: you can add your deployed LLM to the Proxy API by creating a new entry in Replicate (using either the API or UI) and setting the URL to your deployed LLM’s endpoint.

## Services Overview

The toolkit consists of the following services (for more details, please check out [Services documentation](./services.md)):

- **Backend App (app)**: Flask backend service container using SQLAlchemy, configured from `.env`, exposes port 5001.
- **Frontend App (streamlit_app)**: Streamlit container with a user interface, configured from `.env`, exposes port 8501.
- **Database (db)**: MySQL database container, configured from `.env`, exposes port 3306.
- **Redis (redis)**: Redis server for caching and task queue, exposes port 6379.
- **Worker (worker)**: Celery worker container using Redis as a message broker, configured from `.env`.
- **Task Scheduler (beat)**: Celery beat scheduler for periodic tasks, configured from `.env`.
