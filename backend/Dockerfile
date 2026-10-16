FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for some Python packages (e.g., psycopg2)
RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*

# Pre-install CPU-only PyTorch to avoid massive 3GB NVIDIA CUDA downloads which cause SSL/Hash mismatches
RUN pip install --default-timeout=1000 --trusted-host pypi.org --trusted-host download.pytorch.org torch torchvision --index-url https://download.pytorch.org/whl/cpu

# Install python dependencies
COPY requirements.txt /tmp/requirements.txt
RUN pip install --default-timeout=1000 --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r /tmp/requirements.txt

# The application code will be mounted as a volume during development
