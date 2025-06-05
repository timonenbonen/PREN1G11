import RPi.GPIO as GPIO
import time
import serial
import requests
from datetime import datetime

# Setup GPIO only once
GPIO.setmode(GPIO.BCM)
GPIO.setup(23, GPIO.OUT)  # LED flash
GPIO.setup(24, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)  # Start button
GPIO.setup(25, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)  # Position bit 0
GPIO.setup(8, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)   # Position bit 1

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

def send_uart_command(command):
    try:
        ser = serial.Serial("/dev/serial0", 9600, timeout=1)
        ser.write((command + "\r\n").encode())  # Optional newline
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
    0,1,2,3,4,5,6,7,8,9,10,11,12
    for i in range(28):
        print(GPIO.input(i))
    bit0 = GPIO.input(25)
    bit1 = GPIO.input(8)
    start = GPIO.input(24) == GPIO.HIGH

    return ("end")

