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



def special_command(code: int, action: int, value: int):
    send_uart_command(f"({code},{action},{value};)")

def turn_left(duration_ms: int):
    send_uart_command(f"(10,0,{duration_ms};)")

def turn_right(duration_ms: int):
    send_uart_command(f"(11,0,{duration_ms};)")

def turn_left_to_line(skip_count: int):
    send_uart_command(f"(20,0,{skip_count};)")

def turn_right_to_line(skip_count: int):
    send_uart_command(f"(21,0,{skip_count};)")

def follow_line():
    send_uart_command(f"(50,0,0;)")

def drive_backwards():
    send_uart_command(f"(51,0,0;)")

def drive(direction: str, line_skips: int, obstacle: bool):
    assert direction in ['l', 'r', 'n']
    send_uart_command(f"({direction},{line_skips},{int(obstacle)};)")



def send_uart_command(command: str):
    try:
        print(f"[UART] Sending command: {command}")
        with serial.Serial("/dev/serial0", 9600, timeout=1) as ser:
            ser.reset_input_buffer()
            ser.write((command + "\n").encode())

            start_time = time.time()
            timeout_seconds = 5

            while True:
                if ser.in_waiting:
                    response = ser.readline().decode().strip()
                    if response:
                        print(f"[UART] Received response: {response}")
                        handle_uart_response(response)
                        print("uart", "info", "Received UART response", {"response": response})
                        break

                if time.time() - start_time > timeout_seconds:
                    print("[UART] Timeout waiting for response from MCU.")
                    print("uart", "error", "Timeout waiting for response from MCU")
                    break

                time.sleep(0.1)
    except serial.SerialException as e:
        print(f"[Communication] UART error: {e}")
        print("uart", "error", "UART communication failed", {"exception": str(e)})


def handle_uart_response(response: str):
    if response == "end;":
        print("[MCU] Reached end of command.")
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
        1: "C",
        2: "A",
        3: "B",
    }
    return mapping.get(binary, "?")
