import RPi.GPIO as GPIO
import time
import serial
import requests
from datetime import datetime

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
    #if command not in ["TURN", "DRIVE", "STOP", ]:
      #  print(f"[Communication] Invalid command: {command}")
       # return

    #print(f"[Communication] Sending UART command: {command}")
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

        # Use BCM numbering
        GPIO.setmode(GPIO.BCM)

        # Setup pins
        GPIO.setup(23, GPIO.OUT)  # LED flash
        GPIO.setup(24, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)  # Start button
        GPIO.setup(25, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)  # Position bit 0
        GPIO.setup(8, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)  # Position bit 1


def flash_led(times=3, duration=0.2):
    for _ in range(times):
        GPIO.output(23, GPIO.HIGH)
        time.sleep(duration)
        GPIO.output(23, GPIO.LOW)
        time.sleep(duration)

# Read start signal
def wait_for_start():
    print("Waiting for start signal on GPIO 24...")
    while GPIO.input(24) == GPIO.HIGH:
        time.sleep(0.1)
    print("Start signal received!")

# Read position input (3 states: 0-3)
def read_position():
    bit0 = GPIO.input(25)
    bit1 = GPIO.input(8)
    return (bit1 << 1) | bit0

try:
    wait_for_start()
    flash_led()

    while True:
        pos = read_position()
        print(f"Position state: {pos}")
        time.sleep(0.5)

except KeyboardInterrupt:
    print("Exiting gracefully...")

finally:
    GPIO.cleanup()