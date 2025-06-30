import RPi.GPIO as GPIO
import time
import serial
import requests
from roboter_final import communication
from roboter_final.CheckConection import  CheckConnection
from roboter_final.get_picture import capture_picture_from_api
import os
from roboter_final.YoloDetector import YoloDetector
from roboter_final.DegreeInMs import Degree2Milliseconds



BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PICTURES = os.path.join(BASE_DIR, "dataset")

def uart_response_obstructed():
    communication.drive_backwards()
    img_path = capture_picture_from_api(f"{PICTURES}/obstructed.jpg")
    txt_path = YoloDetector.detect_and_save(f"{PICTURES}/obstructed.txt")

    pruefer = CheckConnection(image_path=img_path, txt_path=txt_path).check_connection()

    if pruefer == 0:
        print("Keine Linie")
    elif pruefer == 1:
        print("Verbindung OK")
        communication.special_command(0, 50, 0)
    elif pruefer == 2:
        print("Verbingung und hindernis")
        communication.special_command(0, 50, 1)
    elif pruefer == 3:
        print("Hindernis")
        communication.turn_left(Degree2Milliseconds().turn_degrees_to_ms(180))
        communication.special_command(0, 50, 0)
        communication.turn_right(Degree2Milliseconds().turn_degrees_to_ms(180))


