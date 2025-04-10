# log_server.py
from fastapi import FastAPI, Request
from pydantic import BaseModel
from datetime import datetime
import os
import json

app = FastAPI()

LOG_DIR = "/logs"
os.makedirs(LOG_DIR, exist_ok=True)

class LogEntry(BaseModel):
    source: str  # e.g., "admin", "calculate-route"
    level: str   # e.g., "INFO", "ERROR"
    message: str
    payload: dict | None = None

@app.post("/log")
async def log(entry: LogEntry):
    timestamp = datetime.utcnow().isoformat()
    log_data = {
        "timestamp": timestamp,
        "source": entry.source,
        "level": entry.level,
        "message": entry.message,
        "payload": entry.payload,
    }

    log_file = os.path.join(LOG_DIR, f"{entry.source}.log")
    with open(log_file, "a") as f:
        f.write(json.dumps(log_data) + "\n")

    return {"status": "logged"}

@app.get("/logs")
def get_logs(source: Optional[str] = None):
    logs = []

    if source:
        sources = [source]
    else:
        sources = [f.replace(".log", "") for f in os.listdir(LOG_DIR) if f.endswith(".log")]

    for s in sources:
        log_file = os.path.join(LOG_DIR, f"{s}.log")
        if os.path.isfile(log_file):
            with open(log_file, "r") as f:
                logs.extend(json.loads(line) for line in f)

    logs.sort(key=lambda x: x["timestamp"], reverse=True)  # newest first
    return logs