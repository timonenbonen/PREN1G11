import time
from picamera2 import Picamera2

class Camera:
    def __init__(self, resolution=(1280, 720)):
        self.picam2 = Picamera2()
        config = self.picam2.create_still_configuration(main={"size": resolution})
        self.picam2.configure(config)
        self.picam2.start()
        time.sleep(0.3)

    def capture(self, path: str):
        self.picam2.capture_file(path)

    def close(self):
        self.picam2.close()