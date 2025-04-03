import time


def signal_error():
    print("[OutputHandler] Error LED ON")
    # Simulate GPIO code for blinking or steady error signal
    time.sleep(1)


def signal_arrival():
    print("[OutputHandler] Arrival LED ON")
    # Simulate arrival LED on
    time.sleep(1)