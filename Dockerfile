FROM python:3.11-slim

WORKDIR /app

# Copy requirements first
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir flask gunicorn groq

# Copy application
COPY app.py .

# Run the app
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:app"]
