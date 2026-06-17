FROM python:3.13-slim

# Install system dependencies for PostgreSQL and building packages
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install uv directly from the official binary distribution
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /code

# Copy dependency configuration files first to utilize Docker layer caching
COPY pyproject.toml uv.lock /code/

# Install dependencies globally inside the container using uv
RUN uv pip install --system -r pyproject.toml

# Copy the rest of the application code
COPY . /code/

# Expose Django's internal port
EXPOSE 8000

# Run the web server via uv using the Gunicorn command from your Procfile
CMD ["gunicorn", "config.wsgi", "--bind", "0.0.0.0:8000"]
