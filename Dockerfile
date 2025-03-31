# Use an official lightweight Python image
FROM python:3.11-alpine as builder

# Set working directory
WORKDIR /app

# Install system dependencies for psutil and other compiled packages
RUN apk add --no-cache gcc musl-dev linux-headers python3-dev

# Install dependencies system-wide (without --user)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Expose the port
EXPOSE 7171

# Set environment variables for performance
ENV PYTHONUNBUFFERED=1
ENV PYTHONOPTIMIZE=1

# Ensure Gunicorn is installed and available in the system PATH
RUN which gunicorn

# Use Gunicorn with Uvicorn workers
CMD ["gunicorn", "-w", "2", "-k", "uvicorn.workers.UvicornWorker", "--threads", "2", "--bind", "0.0.0.0:7171", "--worker-tmp-dir", "/dev/shm", "app:app"]
