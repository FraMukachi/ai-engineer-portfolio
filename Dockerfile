FROM python:3.11-slim

WORKDIR /app

# Copy requirements first
COPY requirements.txt .

# Install ALL dependencies including groq
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install groq

# Copy the rest of the app
COPY . .

# Run the app
CMD ["python", "app.py"]
