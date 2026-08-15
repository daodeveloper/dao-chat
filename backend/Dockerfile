# syntax=docker/dockerfile:1.4
FROM python:3.9

WORKDIR /app

# Set pip cache directory for better caching
ENV PIP_CACHE_DIR=/root/.cache/pip

# Copy only requirements first to leverage Docker layer caching
# This layer will be cached unless requirements.txt changes
COPY requirements.txt .

# Install dependencies with BuildKit cache mount for persistent pip cache
# This cache persists between builds, dramatically speeding up subsequent deployments
# The --mount=type=cache creates a persistent cache that survives container rebuilds
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --cache-dir=/root/.cache/pip -r requirements.txt

# Create directories
RUN mkdir -p /app/data/faiss_index

# Copy application code (this invalidates cache if code changes)
COPY app/ /app/app/
COPY data/ /app/data/

RUN chmod -R 755 /app

CMD ["sh", "-c", "python -m app.build_index_simple ; uvicorn app.main:app --host 0.0.0.0 --port 8080"]
