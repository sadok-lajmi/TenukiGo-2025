FROM python:3.12-slim-bookworm

WORKDIR /app

# Install system dependencies (OpenCV needs some libraries)
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --default-timeout=1000 --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Create uploads directory and models directory
RUN mkdir -p /app/uploads /app/models

# Expose port
EXPOSE 5001

# Run the FastAPI application with uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5001"]