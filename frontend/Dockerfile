FROM python:3.11-slim
COPY --from=ghcr.io/astral-sh/uv:0.4.29 /uv /uvx /bin/

WORKDIR /app

COPY requirements.txt ./

RUN uv pip install --no-cache-dir -r requirements.txt --system

COPY . .

RUN touch /app/.streamlit/secrets.toml

EXPOSE 8501

CMD ["streamlit", "run", "home.py"]
