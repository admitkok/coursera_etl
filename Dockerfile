FROM python:3.9-slim

WORKDIR /app

# Copy requirements first
COPY src/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/coursera_etl.py .

ENV PORT 8080
ENV PYTHONUNBUFFERED TRUE

CMD ["gunicorn", "--bind", ":$PORT", "--workers", "1", "--threads", "8", "coursera_etl:run_etl"]