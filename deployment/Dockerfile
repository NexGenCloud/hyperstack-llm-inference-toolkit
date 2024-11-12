FROM python:3.11-slim
COPY --from=ghcr.io/astral-sh/uv:0.4.29 /uv /uvx /bin/

WORKDIR /app

# Install nc, mariadb-client
RUN apt-get update && apt-get install -y netcat-traditional mariadb-client

COPY requirements.txt requirements.txt
RUN uv pip install --no-cache-dir -r requirements.txt --system

COPY . /app

RUN chmod +x /app/scripts/deploy.sh

# Run app.py when the container launches
CMD ["sh", "/app/scripts/deploy.sh"]
