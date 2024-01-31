# Use an official Python base image from the Docker Hub
FROM python:3.12-slim

RUN apt-get update && \
    apt-get install -y build-essential pkg-config libopenblas-dev && \
    rm -rf /var/lib/apt/lists/*


# Set environment variables
ENV PIP_NO_CACHE_DIR=yes \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Install the required python packages globally
ENV PATH="$PATH:/root/.local/bin"
COPY requirements.txt .
RUN CMAKE_ARGS="-DLLAMA_BLAS=ON -DLLAMA_BLAS_VENDOR=OpenBLAS" pip install --no-cache-dir -r requirements.txt

WORKDIR /app
COPY . /app

# Specify the command to run your Python app
CMD ["python", "magi.py"]

