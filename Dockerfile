# Use an official Python runtime as a parent image
# Using slim variant for smaller image size and reduced attack surface
FROM python:3.11-slim

# Set environment variables
# PYTHONDONTWRITEBYTECODE: Prevents Python from writing pyc files to disc
# PYTHONUNBUFFERED: Prevents Python from buffering stdout and stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file first to leverage Docker cache
COPY requirements.txt .

# Install dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Create a non-root user and switch to it for security
RUN useradd -m appuser
USER appuser

# Copy the application code with correct ownership
COPY --chown=appuser:appuser etl.py .

# Run the application
CMD ["python", "etl.py"]
