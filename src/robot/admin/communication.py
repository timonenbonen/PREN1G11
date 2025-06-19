import RPi.GPIO as GPIO
import time
import serial
import requests
from datetime import datetime

# Setup GPIO only once
GPIO.setmode(GPIO.BCM)
GPIO.setup(23, GPIO.OUT)  # LED flash
GPIO.setup(24, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Start button
GPIO.setup(25, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Position bit 0
GPIO.setup(8, GPIO.IN, pull_up_down=GPIO.PUD_UP)   # Position bit 1

def calculate_route():
    try:
        response = requests.post("http://host.docker.internal:8000/take_picture", timeout=10)
        response.raise_for_status()
        data = response.json()
        print(f"[Communication] Route API response: {data}")
        return data["status"], data.get("path", [])
    except requests.RequestException as e:
        print(f"[Communication] Route API error: {e}")
        return "error", []

def encode_drive_command(direction: str, line_skips: int, obstacle: bool) -> str:
    assert direction in ['l', 'r', 'n']
    return f"({direction},{line_skips},{int(obstacle)};)"


def encode_special_command(code: int, action: int, value: int) -> str:
    return f"(0,{code},{value};)"

def turn_left(duration_ms: int) -> str:
    return encode_special_command(10, 0, duration_ms)

def turn_right(duration_ms: int) -> str:
    return encode_special_command(11, 0, duration_ms)

def turn_left_to_line(skip_count: int) -> str:
    return encode_special_command(20, 0, skip_count)

def turn_right_to_line(skip_count: int) -> str:
    return encode_special_command(21, 0, skip_count)

def follow_line() -> str:
    return encode_special_command(50, 0, 0)

def drive_backwards() -> str:
    return encode_special_command(51, 0, 0)



def send_uart_command(command: str):
    try:
        print(command)
        ser = serial.Serial("/dev/serial0", 9600, timeout=1)
        ser.write((command + "\n").encode())  # Optional newline
        ser.close()
    except serial.SerialException as e:
        print(f"[Communication] UART error: {e}")

def handle_uart_response(response: str):
    if response == "end;":
        print("[MCU] Reached end of command.")
        # Trigger next navigation step
    elif response == "unknown;":
        print("[MCU] Unknown command received. Consider retrying or debugging.")
    elif response == "obstructed;":
        print("[MCU] Unexpected obstacle detected!")
        
    else:
        print(f"[MCU] Unhandled response: {response}")

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

def flash_led(times=3, duration=0.2):
    for _ in range(times):
        GPIO.output(23, GPIO.HIGH)
        time.sleep(duration)
        GPIO.output(23, GPIO.LOW)
        time.sleep(duration)

def wait_for_start():
    print("Waiting for start signal on GPIO 24...")
    while GPIO.input(24) == GPIO.HIGH:
        time.sleep(0.1)
    print("Start signal received!")

def read_position():
    bit0 = GPIO.input(25)
    bit1 = GPIO.input(8)
    binary = (bit1 << 1) | bit0  # ergibt 0–3

    mapping = {
        1: "A",
        2: "B",
        3: "C",
    }
    return mapping.get(binary, "?")
