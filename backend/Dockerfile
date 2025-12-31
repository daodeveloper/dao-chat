FROM python:3.9

WORKDIR /app

# Set pip cache directory for better caching
ENV PIP_CACHE_DIR=/root/.cache/pip

# Copy only requirements first to leverage Docker layer caching
# This layer will be cached unless requirements.txt changes
COPY requirements.txt .

# Install dependencies with pip cache enabled
# Docker will cache this layer if requirements.txt hasn't changed
RUN pip install --cache-dir=/root/.cache/pip -r requirements.txt

# Create directories
RUN mkdir -p /app/data/faiss_index

# Copy application code (this invalidates cache if code changes)
COPY app/ /app/app/
COPY data/ /app/data/

RUN chmod -R 755 /app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]