FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libcamera-apps \
    libcamera0 \
    libjpeg62-turbo \
    v4l-utils \
    libatomic1 \
    ffmpeg \
    && apt-get clean

# Set working directory
WORKDIR /app
COPY . /app

# Install Python packages
RUN pip install fastapi uvicorn opencv-python numpy requests

# Default command
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]