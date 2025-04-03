
import serial
import requests

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
    print(f"[Communication] Sending UART command: {command}")
    ser = serial.Serial("/dev/serial0", 115200, timeout=1)
    ser.write(command.encode())
    ser.close()