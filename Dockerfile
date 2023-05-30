# Use an official Python base image from the Docker Hub
FROM python:3.10-slim

RUN apt-get update && apt-get install -y firefox-esr

# Set environment variables
ENV PIP_NO_CACHE_DIR=yes \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Install the required python packages globally
ENV PATH="$PATH:/root/.local/bin"
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /app
COPY . /app

# Specify the command to run your Python app
CMD ["python", "magi.py"]

