FROM python:3.11-slim

WORKDIR /app

# Install dependencies first (better layer caching)
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the backend
COPY backend/ .

# SQLite DB will live in a mounted volume at /data
RUN mkdir -p /data
ENV ARGUS_DATABASE_URL=sqlite:////data/argus.db
ENV ARGUS_GEMINI_EVAL_MODEL=gemini-2.5-flash
ENV ARGUS_USE_MOCK_CARDS=true
ENV ARGUS_CORS_ORIGINS=https://argus-principia.vercel.app,https://34-16-41-18.sslip.io
ENV ARGUS_JWT_SECRET=argus-hackathon-prod-secret-2026

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
