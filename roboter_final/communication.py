import RPi.GPIO as GPIO
import time
import serial
import requests
from datetime import datetime
from roboter_final.handle_uart_responses import *

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

    return send_uart_command(f"{code},{action},{value};")


def turn_left(duration_ms: int):
    send_uart_command(f"0,10,{duration_ms};")

def turn_right(duration_ms: int):
    send_uart_command(f"0,11,{duration_ms};")

def turn_left_to_line(skip_count: int):
    send_uart_command(f"0,20,{skip_count};")

def turn_right_to_line(skip_count: int):
    send_uart_command(f"0,21,{skip_count};")

def follow_line():
    send_uart_command(f"0,50,0;")

def drive_backwards():
    send_uart_command(f"0,51,0;")

def drive(direction: str, line_skips: int, obstacle: bool):
    assert direction in ['l', 'r', 'n']
    send_uart_command(f"{direction},{line_skips},{int(obstacle)};")



def send_uart_command(command: str):
    try:
        print(f"[UART] Sending command: {command}")
        with serial.Serial("/dev/serial0", 9600, timeout=1) as ser:
            ser.reset_input_buffer()
            ser.write((command + "\n").encode())

            start_time = time.time()
            timeout_seconds = 30

            waiting_for_final_response = False

            while True:
                if ser.in_waiting:
                    response = ser.readline().decode().strip()
                    if response:
                        print(f"[UART] Received response: {response}")

                        if response == "ok;":
                            print("[MCU] Command acknowledged. Waiting for completion...")
                            waiting_for_final_response = True  # Wait for "end;" or "obstructed;"
                            continue

                        message = handle_uart_response(response)
                        print("uart", "info", "Received UART response", {"response": response})
                        time.sleep(0.1)
                        return message


                if time.time() - start_time > timeout_seconds:
                    print("[UART] Timeout waiting for response from MCU.")
                    print("uart", "error", "Timeout waiting for response from MCU")
                    break

                time.sleep(0.1)


    except serial.SerialException as e:
        print(f"[Communication] UART error: {e}")
        print("uart", "error", "UART communication failed", {"exception": str(e)})
    return 1

def handle_uart_response(response: str):
    if response == "end;":
        print("[MCU] Command completed successfully.")
    elif response == "obstructed;":
        print("[MCU] Unexpected obstacle detected! Handle accordingly.")
        uart_response_obstructed()
    elif response == "no line;":
        return 0


    else:
        print(f"[MCU] Unhandled response: {response}")
    return 1

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
