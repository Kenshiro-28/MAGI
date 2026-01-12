FROM debian:stable-slim

RUN apt-get update && \
    apt-get install -y build-essential apparmor-utils git pkg-config libopenblas-dev python3-venv \
    python3-pip python3-requests python3-pycurl python3-protego antiword python3-bs4 python3-docx \
    python3-odf python3-pypdf python3-python-telegram-bot && \
    rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PIP_NO_CACHE_DIR=yes \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Create a Python virtual environment
RUN python3 -m venv /opt/venv --system-site-packages
ENV PATH="/opt/venv/bin:$PATH"

# Install Python packages
COPY requirements.txt .
RUN CMAKE_ARGS="-DGGML_BLAS=ON -DGGML_BLAS_VENDOR=OpenBLAS" pip install -r requirements.txt

WORKDIR /app
COPY . /app

CMD ["python", "magi.py"]

