
import serial
import requests
from datetime import datetime

def calculate_route():
    try:
        response = requests.post("http://calculate-route:8000/calculate", timeout=10)
        response.raise_for_status()
        data = response.json()
        print(f"[Communication] Route API response: {data}")
        return data["status"], data.get("path", [])
    except requests.RequestException as e:
        print(f"[Communication] Route API error: {e}")
        return "error", []

def send_uart_command(command):
    if command not in ["TURN", "DRIVE", "STOP"]:
        print(f"[Communication] Invalid command: {command}")
        return

    print(f"[Communication] Sending UART command: {command}")
    try:
        ser = serial.Serial("/dev/serial0", 9600, timeout=1)
        ser.write((command + "\n").encode())  # Optional newline for microcontroller parsing
        ser.close()
    except serial.SerialException as e:
        print(f"[Communication] UART error: {e}")


def log_event(source, level, message, payload=None):
    try:
        requests.post("http://log-server:9000/log", json={
            "source": source,
            "level": level,
            "message": message,
            "payload": payload
        })
    except requests.RequestException as e:
        print(f"[{source}] Failed to log: {e}")