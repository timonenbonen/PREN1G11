import os
import random
import cv2
from ultralytics import YOLO

# Pfade anpassen
MODEL_PATH = r'C:\Users\marin\PycharmProjects\PREN1G11\src\utils\tests\YoloModells\model=yolov8npt epochs=100 imgsz=640\my_model.pt'  # <-- Hier anpassen
IMAGE_FOLDER = r'C:\Users\marin\PycharmProjects\PREN1G11\src\utils\tests\Bilder\MusterBoden'  # <-- Hier anpassen
THRESHOLD = 0.5  # Mindest-Konfidenz für eine Anzeige

# Modell laden
if not os.path.exists(MODEL_PATH):
    print(f'Fehler: Modell nicht gefunden unter {MODEL_PATH}')
    exit()

model = YOLO(MODEL_PATH)
labels = model.names  # Klassenlabels


# Funktion zum Zufallsbild holen
def get_random_image(folder):
    images = [f for f in os.listdir(folder) if f.lower().endswith(('png', 'jpg', 'jpeg'))]
    if not images:
        print('Fehler: Keine Bilder im Ordner gefunden.')
        exit()
    return os.path.join(folder, random.choice(images))


while True:
    image_path = get_random_image(IMAGE_FOLDER)
    frame = cv2.imread(image_path)
    if frame is None:
        print(f'Fehler beim Laden: {image_path}')
        continue

    # YOLO Inferenz
    results = model(frame, verbose=False)
    detections = results[0].boxes

    for det in detections:
        xmin, ymin, xmax, ymax = map(int, det.xyxy[0])
        conf = det.conf.item()
        classidx = int(det.cls.item())
        classname = labels[classidx]

        if conf > THRESHOLD:
            cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), (0, 255, 0), 2)
            label = f'{classname}: {int(conf * 100)}%'
            cv2.putText(frame, label, (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    cv2.imshow('YOLO Detection', frame)
    key = cv2.waitKey(0) & 0xFF
    if key == ord('q'):
        break

cv2.destroyAllWindows()
