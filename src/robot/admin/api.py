from fastapi import FastAPI, Response
from communication import calculate_route, send_uart_command
from output_handler import signal_arrival, signal_error
import requests


app = FastAPI()
status = "idle"  # global robot state


@app.post("/run")
def run_robot():
    global status
    status = "running"

    try:
        result = calculate_route()

        if result == "valid":
            send_uart_command("DRIVE")
        else:
            send_uart_command("TURN")
            signal_error()

        signal_arrival()
        status = "done"
        return {"status": "success", "result": result}

    except Exception as e:
        status = "error"
        return {"status": "error", "message": str(e)}


@app.get("/status")
def get_status():
    return {"status": status}

@app.get("/test-picture")
def test_picture():
    try:
        resp = requests.get("http://calculate-route:8000/take_picture", timeout=10)
        resp.raise_for_status()

        return Response(
            content=resp.content,
            media_type=resp.headers.get("Content-Type", "image/jpeg")
        )

    except requests.RequestException as e:
        return {"error": f"Could not get picture: {e}"}