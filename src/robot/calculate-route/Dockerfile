FROM python:3.11-slim

RUN apt-get update && apt-get install -y libgl1 libglib2.0-0

WORKDIR /app
COPY . /app

RUN pip install fastapi uvicorn opencv-python numpy

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]