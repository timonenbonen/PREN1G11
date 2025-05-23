from fastapi import FastAPI, Response
from communication import calculate_route, send_uart_command, log_event
from output_handler import signal_arrival, signal_error
import requests
from pydantic import BaseModel
import time
from fastapi.staticfiles import StaticFiles



class TestRunRequest(BaseModel):
    option: str

app = FastAPI()
app.mount("/", StaticFiles(directory="../static", html=True), name="static")
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
@app.post("/command")
def command_robot(req: CommandRequest):
    # Log the incoming command
    log_event("admin", "INFO", f"Command triggered: {req.option}")

    # Predefined mapping for simple commands
    mapping = {
        "turn left": "TURN_LEFT",
        "turn right": "TURN_RIGHT",
        "follow line": "FOLLOW_LINE",
        "backwards predefined": "BACKWARD_PREDEFINED",
    }

    if req.option == "forward":
        # Block until the start button is pressed
        if input_handler.wait_for_start_button():
            route_status, path = communication.calculate_route()
            log_event("admin", "INFO", "Route calculated", {"status": route_status, "path": path})

            if route_status == "valid":
                communication.send_uart_command(f"DRIVE:{path}")
                log_event("admin", "INFO", f"Sent DRIVE command with path {path}")
            else:
                communication.send_uart_command("TURN")
                output_handler.signal_error()
                log_event("admin", "WARNING", "Invalid route: sent TURN and signaled error")

            output_handler.signal_arrival()
            log_event("admin", "INFO", "Arrival signaled")
        else:
            return {"status": "error", "message": "Start button not pressed"}

    else:
        cmd = mapping.get(req.option)
        if not cmd:
            log_event("admin", "WARNING", f"Unknown command: {req.option}")
            return {"status": "error", "message": "Unknown command"}

        communication.send_uart_command(cmd)
        log_event("admin", "INFO", f"Sent {cmd} command to UART")

    return {"status": "success", "command": req.option}

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