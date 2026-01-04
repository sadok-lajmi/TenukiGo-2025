# Choosing the stable version: Python 3.12 on Debian 12 (Bookworm)
FROM python:3.12-slim-bookworm

WORKDIR /app

# 1. Install system dependencies
# - build-essential & git: to clone and build sente
# - libgl1 & libglib2.0-0: for OpenCV
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 2. Install Python build tools
RUN pip install --no-cache-dir --upgrade pip setuptools wheel pybind11 meson ninja numpy

# 3. MANUAL INSTALLATION OF SENTE (With Patches)
# Clone, patch, install, then clean up.
RUN git clone https://github.com/atw1020/sente.git sente-src && \
    cd sente-src && \
    # PATCH A: Modify setup.py (replace '>=3.8.*' with '>=3.8')
    sed -i 's/python_requires=">=3.8.*"/python_requires=">=3.8"/' setup.py && \
    # PATCH B: Add #include <algorithm> in Tree.h and SGFNode.cpp
    # Insert the line at the very beginning of the file (line 1)
    sed -i '1i #include <algorithm>' src/Utils/Tree.h && \
    sed -i '1i #include <algorithm>' src/Utils/SGF/SGFNode.cpp && \
    # Installation
    pip install --no-build-isolation . && \
    # Cleanup
    cd .. && \
    rm -rf sente-src

# 4. Install other dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Final configuration
COPY . .
ENV PYTHONPATH=/app

# Create necessary folders
RUN mkdir -p /app/storage/videos 

# Launch the service
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000"]
