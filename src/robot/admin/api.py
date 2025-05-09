from fastapi import FastAPI, Response
from communication import calculate_route, send_uart_command, log_event
from output_handler import signal_arrival, signal_error
import requests
from pydantic import BaseModel
import time

class TestRunRequest(BaseModel):
    option: str

app = FastAPI()
status = "idle"  # global robot state
option: str

@app.post("/run")
def run_robot():
    global status
    status = "running"
    log_event("admin", "INFO", "Run triggered")

    try:
        result, path = calculate_route()
        log_event("admin", "INFO", "Route calculation result", {"status": result, "path": path})

        if result == "valid":
            send_uart_command("DRIVE")
            log_event("admin", "INFO", "Sent DRIVE command to UART")
        else:
            send_uart_command("TURN")
            signal_error()
            log_event("admin", "WARNING", "Sent TURN command due to invalid route")

        signal_arrival()
        log_event("admin", "INFO", "Arrival signaled")

        status = "done"
        return {"status": "success", "result": result}

    except Exception as e:
        status = "error"
        log_event("admin", "ERROR", "Exception during run", {"error": str(e)})
        return {"status": "error", "message": str(e)}


@app.get("/status")
def get_status():
    return {"status": status}

@app.get("/test-picture")
def test_picture():
    try:
        resp = requests.get("http://host.docker.internal:8000/take_picture", timeout=10)
        resp.raise_for_status()

        return Response(
            content=resp.content,
            media_type=resp.headers.get("Content-Type", "image/jpeg")
        )

    except requests.RequestException as e:
        return {"error": f"Could not get picture: {e}"}


@app.post("/testrun")
def testrun(req: TestRunRequest):
    option = req.option.upper()

    if option == "A":
        send_uart_command("DRIVE")
        time.sleep(1)
        send_uart_command("STOP")
        time.sleep(2)
        send_uart_command("TURNR")
        time.sleep(1)
        send_uart_command("STOP")
        time.sleep(2)
        send_uart_command("TURNL")
        time.sleep(1)
        send_uart_command("STOP")
    elif option == "B":
        send_uart_command("DRIVE")
        time.sleep(2)
        send_uart_command("STOP")
    elif option == "C":
        send_uart_command("TURNR")
        time.sleep(2)
        send_uart_command("STOP")
        time.sleep(2)
        send_uart_command("DRIVE")
        time.sleep(2)
        send_uart_command("STOP")
    else:
        return {"status": "error", "message": f"Unknown option '{option}'"}

    return {"status": "success", "executed": option}