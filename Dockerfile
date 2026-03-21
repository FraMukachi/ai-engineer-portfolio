FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run migrations and collect static
RUN python manage.py migrate
RUN python manage.py collectstatic --noinput

# Use gunicorn with the combined app
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "wsgi:app"]
