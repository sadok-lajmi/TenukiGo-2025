# Python 3.12-slim based on Debian 12 (Bookworm)
FROM python:3.12-slim-bookworm

WORKDIR /app

# 1. System dependencies
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    libzip4 \
    libgomp1 \
    libssl-dev \
    file \
    && rm -rf /var/lib/apt/lists/*

# 2. Environment Setup
ENV MODEL_DIR="/app/model"
ENV NEURALNET_DIR="/app/neuralnet"
ENV CONFIG_DIR="/app/configs"
ENV KATAGO_BIN_DIR="/app/katago-bin"

# Env vars for Python application
ENV GOINSIGHT_BASE_DIR="/app"
ENV KATAGO_MODEL_DIR="${MODEL_DIR}"
ENV KATAGO_NEURALNET_DIR="${NEURALNET_DIR}"
ENV KATAGO_CONFIG_DIR="${CONFIG_DIR}"

RUN mkdir -p ${MODEL_DIR} ${NEURALNET_DIR} ${CONFIG_DIR} ${KATAGO_BIN_DIR}

# 3. KataGo Setup (Linux Eigen AppImage)
ENV KATAGO_RELEASE_URL="https://github.com/lightvector/KataGo/releases/download/v1.16.3/katago-v1.16.3-eigen-linux-x64.zip"
ENV NEURALNET_URL="https://katagoarchive.org/g170/neuralnets/g170e-b10c128-s1141046784-d204142634.bin.gz"

WORKDIR ${KATAGO_BIN_DIR}

# Download KataGo Zip
RUN wget -q ${KATAGO_RELEASE_URL} -O katago.zip

# Unzip (It contains 'katago' AppImage and other files at root of zip usually)
RUN unzip -o katago.zip

# Extract AppImage
# The binary is named 'katago' from the zip.
RUN chmod +x katago && \
    ./katago --appimage-extract

# Create a symlink to the true executable (AppRun)
# This allows python to call /app/model/katago as if it were the binary.
RUN ln -s ${KATAGO_BIN_DIR}/squashfs-root/AppRun ${MODEL_DIR}/katago

# Cleanup zip
RUN rm katago.zip

# Download Neural Net
WORKDIR ${NEURALNET_DIR}
RUN wget -q ${NEURALNET_URL} -O g170e-b10c128-s1141046784-d204142634.bin.gz

# Download Config
# We need a valid analysis config. Using default_gtp.cfg pattern but suited for analysis.
# For simplicity, we can fetch a standard one or create a minimal one.
# https://github.com/lightvector/KataGo/blob/master/cpp/configs/analysis_example.cfg
WORKDIR ${CONFIG_DIR}
RUN wget -q https://raw.githubusercontent.com/lightvector/KataGo/master/cpp/configs/analysis_example.cfg -O fast_game_analysis.cfg
# Also need deep_analysis.cfg for the deep endpoint if it differs, but we can reuse or copy.
RUN cp fast_game_analysis.cfg deep_analysis.cfg

# 4. Python Setup
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 5. App Code
COPY . .

# Expose API Port
EXPOSE 5002

# Run
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "5002"]
