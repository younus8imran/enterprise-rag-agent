# Dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Copy dependency files first
COPY pyproject.toml uv.lock* requirements.txt ./

# Install dependencies (excluding dev dependencies for production)
RUN uv pip install --system -r requirements.txt email-validator mistralai python-multipart psycopg2-binary

# Copy the rest of the application
COPY . .

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
