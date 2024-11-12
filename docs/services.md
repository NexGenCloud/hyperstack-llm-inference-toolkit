# Services Overview - Hyperstack LLM Inference Toolkit

The Hyperstack LLM Inference Toolkit consists of the following services:

## 1. Backend App (app):

- **Description**: This is the main backend service container, built using Flask and SQLAlchemy for database access.
- **Dockerfile**: [Dockerfile](./backend/Dockerfile)
- **Environment**: Configured with settings from [.env](./.env) file.
- **Ports**: Exposes port 5001.
- **Execution**: Runs scripts to wait for the database and then starts the application.

## 2. Frontend App (streamlit_app):

- **Description**: This container runs a Streamlit application, providing a user-friendly interface for interacting with the toolkit.
- **Dockerfile**: [Dockerfile](./frontend/Dockerfile)
- **Environment**: Configured with settings from [.env](./.env) file.
- **Ports**: Exposes port 8501.
- **Execution**: Runs the Streamlit application.

## 3. Database (db):

- **Description**: MySQL database for storing application data.
- **Image**: mysql:9.0
- **Environment**: Configured with settings from [.env](./.env) file.
- **Ports**: Exposes port 3306.
- **Execution**: Runs the MySQL server.

## 3. Redis (redis):

- **Description**: Redis server for caching and Celery task queue.
- **Image**: redis:bookworm
- **Ports**: Exposes port 6379.
- **Execution**: Runs the Redis server.

## 4. Worker (worker):

- **Description**: This container runs a Celery worker, responsible for handling asynchronous tasks sent by the backend application (app). It uses Redis as the message broker to queue and manage tasks.
- **Dockerfile**: [Dockerfile](./backend/Dockerfile)
- **Environment**: Configured with settings from [.env](./.env) file.
- **Execution**: Runs the Celery worker command, which continuously listens for tasks from Redis and processes them asynchronously.

## 5. Task Scheduler (beat):

- **Description**: This service runs a Celery beat scheduler, which manages periodic tasks for the application, enabling scheduled task execution at set intervals.
- **Dockerfile**: [Dockerfile](./backend/Dockerfile)
- **Environment**: Configured with settings from [.env](./.env) file.
- **Execution**: Runs the Celery beat command, scheduling tasks by periodically adding them to the Redis queue.
