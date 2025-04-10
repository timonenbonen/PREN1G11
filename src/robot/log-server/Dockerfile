# log-server/Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY log_server.py .
RUN pip install fastapi uvicorn

EXPOSE 9000

CMD ["uvicorn", "log_server:app", "--host", "0.0.0.0", "--port", "9000"]