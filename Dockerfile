# Use lightweight Python base image for ARM
FROM python:3.11-slim

# Install system packages if needed (e.g., GPIO libraries)
RUN apt-get update && apt-get install -y \
    python3-rpi.gpio \
    && rm -rf /var/lib/apt/lists/*

# Set workdir
WORKDIR /app

# Copy your code into the image
COPY . /app

# Install Python dependencies (if you have requirements.txt)
RUN pip install --no-cache-dir -r requirements.txt

# Entry point
CMD ["python", "robot.py"]