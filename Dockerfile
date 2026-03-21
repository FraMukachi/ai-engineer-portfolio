FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV GROQ_API_KEY=""

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .

# Install Python dependencies including Groq
RUN pip install --upgrade pip && \
    pip install --no-cache-dir \
    flask==2.3.3 \
    gunicorn==21.2.0 \
    groq==0.4.2

# Copy application
COPY . .

# Create a non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Run with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "1", "--threads", "2", "app:app"]
