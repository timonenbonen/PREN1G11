import os
import cv2
from ultralytics import YOLO

# Objektklasse für erkannte Elemente
class Objekt:
    def __init__(self, klasse, vertrauen, bounding_box):
        self.klasse = klasse
        self.vertrauen = vertrauen  # Prozentwert
        self.bounding_box = bounding_box  # (x1, y1, x2, y2)
        self.flaeche = self._area()
        self.zentrum = self._center()
        self.buchstabe = None

        if self.klasse in ['pointa', 'pointb', 'pointc']:
            self._assign_letter()

    def _area(self):
        x1, y1, x2, y2 = self.bounding_box
        return (x2 - x1) * (y2 - y1)

    def _center(self):
        x1, y1, x2, y2 = self.bounding_box
        if self.klasse == 'barrier':
            return ((x1 + x2) / 2, y2 - ((x2 - x1) / 2))  # speziell für waagerechte Balken
        return ((x1 + x2) / 2, (y1 + y2) / 2)

    def _assign_letter(self):
        mapping = {'pointa': 'A', 'pointb': 'B', 'pointc': 'C'}
        self.buchstabe = mapping.get(self.klasse)


# YOLO-Erkennungs-Wrapper
class YoloDetector:
    def __init__(self, model_path):
        self.model = YOLO(model_path)
        self.labels = self.model.names

    def detect(self, image_path, confidence_threshold=0.01):
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")

        frame = cv2.imread(image_path)
        if frame is None:
            raise ValueError("Image loading failed.")

        results = self.model(frame, conf=confidence_threshold, verbose=False)
        boxes = results[0].boxes
        detected_objects = []

        for det in boxes:
            x1, y1, x2, y2 = map(int, det.xyxy[0])
            conf = det.conf.item()
            cls_id = int(det.cls.item())
            klass = self.labels[cls_id]
            obj = Objekt(klass, conf * 100, (x1, y1, x2, y2))
            detected_objects.append(obj)
            print(f"Klasse erkannt: {klass}, Vertrauen: {conf:.1f}%, Box: ({x1}, {y1}, {x2}, {y2})")
        return detected_objects

    def save_to_txt(self, objects, path):
        with open(path, 'w', encoding='utf-8') as f:
            for obj in objects:
                f.write(f"{obj.klasse};{obj.vertrauen:.1f}%;{obj.bounding_box};{obj.flaeche};{obj.zentrum};{obj.buchstabe or ''}\n")

    def detect_and_save(self, image_path, save_path="/dataset/detected_objects.txt"):
        objects = self.detect(image_path)
        self.save_to_txt(objects, save_path)

        return objects
