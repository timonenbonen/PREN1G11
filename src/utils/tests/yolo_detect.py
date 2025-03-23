import os
import sys
import argparse
import random
import cv2
import numpy as np
from ultralytics import YOLO

# Argumente parsen
parser = argparse.ArgumentParser()
parser.add_argument('--model', required=True, help='Pfad zum YOLO-Modell')
parser.add_argument('--folder', default=r'C:\Users\marin\Downloads\nurbilder', help='Pfad zum Bilder-Ordner')
parser.add_argument('--thresh', default=0.5, type=float, help='Minimale Konfidenzschwelle')
parser.add_argument('--resolution', default='1280x720', help='Anzeigegröße WxH')
args = parser.parse_args()

# YOLO-Modell laden
if not os.path.exists(args.model):
    print('ERROR: Modell nicht gefunden.')
    sys.exit(0)
model = YOLO(args.model, task='detect')
labels = model.names

# Zufälliges Bild aus dem Ordner auswählen
def get_random_image(folder):
    images = [f for f in os.listdir(folder) if f.lower().endswith(('png', 'jpg', 'jpeg'))]
    if not images:
        print('ERROR: Keine Bilder im Ordner gefunden.')
        sys.exit(0)
    return os.path.join(folder, random.choice(images))

# Auflösung setzen
resW, resH = map(int, args.resolution.split('x'))

while True:
    image_path = get_random_image(args.folder)
    frame = cv2.imread(image_path)
    if frame is None:
        print(f'Fehler beim Laden des Bildes: {image_path}')
        continue

    # Bild auf feste Größe skalieren
    frame = cv2.resize(frame, (resW, resH))

    # YOLO Inferenz
    results = model(frame, verbose=False)
    detections = results[0].boxes
    
    for det in detections:
        xmin, ymin, xmax, ymax = map(int, det.xyxy[0])
        conf = det.conf.item()
        classidx = int(det.cls.item())
        classname = labels[classidx]
        
        if conf > args.thresh:
            cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), (0, 255, 0), 2)
            label = f'{classname}: {int(conf * 100)}%'
            cv2.putText(frame, label, (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    cv2.imshow('YOLO Detection', frame)
    key = cv2.waitKey(0) & 0xFF
    if key == ord('q'):
        break

cv2.destroyAllWindows()
