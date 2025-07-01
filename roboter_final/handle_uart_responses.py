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
    communication.turn_left(Degree2Milliseconds().turn_degrees_to_ms(180))
    communication.special_command(0,50,0)
    communication.turn_left(Degree2Milliseconds().turn_degrees_to_ms(180))



