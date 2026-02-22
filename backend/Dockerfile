FROM python:3.11-slim

WORKDIR /app

# Install dependencies first (better layer caching)
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the backend
COPY backend/ .

# SQLite DB will live in a mounted volume at /data
RUN mkdir -p /data

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
