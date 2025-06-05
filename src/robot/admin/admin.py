import input_handler
import output_handler
import communication
import RPi.GPIO as GPIO

# process_image.py
import requests
import cv2
import numpy as np


def test():
    communication.flash_led(3,0.2)

    communication.send_uart_command("0,51,0;")
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


if __name__ == "__main__":
    GPIO.setmode(GPIO.BCM)
    print(test())
    GPIO.cleanup()

    ##result = process()
