# Use official Python image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY src/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ .

# Set environment variables
ENV PORT 8080
ENV PYTHONUNBUFFERED TRUE

# Run the application
CMD ["gunicorn", "--bind", ":$PORT", "--workers", "1", "--threads", "8", "coursera_etl:run_etl"]