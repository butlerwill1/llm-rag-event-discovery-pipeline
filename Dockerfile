# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set working directory inside container
WORKDIR /app

# Copy requirements first (for better caching)
# If requirements don't change, this layer is cached
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the embedding model during build (saves ~30-60s on startup)
# This adds ~87MB to the image but makes startup instant
# Suppress warnings: HF_HUB_DISABLE_TELEMETRY=1 and TRANSFORMERS_VERBOSITY=error
RUN HF_HUB_DISABLE_TELEMETRY=1 TRANSFORMERS_VERBOSITY=error \
    python -c "from sentence_transformers import SentenceTransformer; \
    import warnings; warnings.filterwarnings('ignore'); \
    SentenceTransformer('all-MiniLM-L6-v2')"

# Copy application code
COPY main.py .
COPY email_service.py .
COPY rag_query.py .
COPY src ./src
COPY data ./data

# Set environment variables (defaults, can be overridden at runtime)
ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    HF_HUB_DISABLE_TELEMETRY=1 \
    TRANSFORMERS_VERBOSITY=error

# Run the application
CMD ["python", "main.py"]
