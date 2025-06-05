import input_handler
import output_handler
import communication
import RPi.GPIO as GPIO

# process_image.py
import requests
import cv2
import numpy as np
import time



def test(uart_command):
    communication.flash_led(3,0.2)

    communication.send_uart_command(uart_command)
    return communication.read_position()



def process():
    communication.wait_for_start()
    image_path = capture_picture_from_api()


    processed_image_path = process_image(image_path)

    model_path = "yoloModels/my_model.pt"

    detector = YoloDetector(model_path)

    detected_objects = detector.detect_and_save(image_path)

    detector.save_to_txt(detected_objects, "/tmp/detected_objects.txt")
    build_matrix_from_detection(txt_path, processed_image_path)

    # Example image processing
    edges = cv2.Canny(image, 100, 200)
    result_path = "/tmp/edges.jpg"
    cv2.imwrite(result_path, edges)

    return result_path

def reset_tof():
    GPIO.setup(7, GPIO.OUT)
    GPIO.output(7, GPIO.LOW)
    time.sleep(1)
    GPIO.output(7, GPIO.HIGH)
    time.sleep(1)
    GPIO.output(7, GPIO.LOW)
    time.sleep(1)

if __name__ == "__main__":
    reset_tof()
    GPIO.setmode(GPIO.BCM)
    first = 0
    second = 10
    third = 1000
    while True:
        first = input("Enter first:")
        second = input("Enter second:")
        third = input("Enter third:")
        if first == "exit":
            break
        if second.isnumeric() and third.isnumeric():
            print(test(f"{first},{second},{third};"))
        else:
            print(f"{first},{second},{third}; wrong input")
    GPIO.cleanup()

    ##result = process()
