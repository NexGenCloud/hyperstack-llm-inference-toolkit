FROM python:3.11-slim
COPY --from=ghcr.io/astral-sh/uv:0.4.29 /uv /uvx /bin/

ARG APP_ENVIRONMENT

WORKDIR /app

# Install nc
RUN apt-get update && apt-get install -y netcat-traditional
RUN apt-get install -y mariadb-client

COPY requirements.txt requirements.txt
RUN uv pip install --no-cache-dir -r requirements.txt --system

COPY . /app/

# Grant execution permissions
RUN chmod +x /app/scripts/entrypoint-${APP_ENVIRONMENT}.sh
RUN chmod +x /app/scripts/wait_for_db.sh

ENV PYTHONPATH=/app

CMD ["/bin/bash", "/app/scripts/entrypoint-${APP_ENVIRONMENT}.sh"]
