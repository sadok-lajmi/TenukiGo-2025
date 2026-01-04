# Use a lightweight but compatible Python version
FROM python:3.12-slim-bookworm

# Set the root working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    libglib2.0-0 \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# --- Folder structure ---
COPY . ./backend

# Add /app to PYTHONPATH
ENV PYTHONPATH=/app

# Create directories for shared uploads
RUN mkdir -p /app/storage/sgf_files /app/storage/videos /app/storage/thumbnails 

# Expose the API port
EXPOSE 8000

# Start the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
