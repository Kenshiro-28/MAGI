FROM debian:stable

RUN apt-get update && \
    apt-get install -y build-essential pkg-config libopenblas-dev python3-venv python3-pip \
      apparmor-utils chromium chromium-driver python3-selenium python3-bs4 python3-docx python3-odf \
      python3-pypdf2 && \
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
RUN CMAKE_ARGS="-DLLAMA_BLAS=ON -DLLAMA_BLAS_VENDOR=OpenBLAS" pip install --no-cache-dir -r requirements.txt

WORKDIR /app
COPY . /app

CMD ["python", "magi.py"]

