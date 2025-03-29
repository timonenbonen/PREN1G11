import cv2
from ultralytics import YOLO

# Alle Definitionen am Anfang
MODEL_PATH = r"C:\Users\marin\PycharmProjects\PREN1G11\src\utils\tests\YoloModells\model=yolov8npt epochs=100 imgsz=640\my_model.pt"
IMAGE_PATH = r"C:\Users\marin\PycharmProjects\PREN1G11\src\utils\tests\Bilder\MusterBoden\Test1.jpg"  # Hier deinen Bildpfad eintragen
CONF_THRESHOLD = 0.1  # Konfidenz-Schwellenwert, kannst du nach Bedarf ändern


def detect_objects(image_path, model_path, conf_threshold):
    # Modell laden
    model = YOLO(model_path)

    # Bild laden
    image = cv2.imread(image_path)
    if image is None:
        print(f"Fehler: Bild konnte nicht geladen werden: {image_path}")
        return []

    # Inferenz durchführen
    results = model(image, conf=conf_threshold)[0]

    # Erkannte Objekte sammeln
    detected_objects = []

    # Durch Ergebnisse iterieren
    for i, (box, score, cls) in enumerate(zip(results.boxes.xyxy, results.boxes.conf, results.boxes.cls)):
        class_name = results.names[int(cls)]
        confidence = float(score)

        # Objekt zur Liste hinzufügen
        detected_objects.append({
            "id": i,
            "class": class_name,
            "confidence": confidence,
            "box": box.tolist()  # Bounding box [x1, y1, x2, y2]
        })

    return detected_objects


# Objekte erkennen mit den oben definierten Parametern
objects = detect_objects(IMAGE_PATH, MODEL_PATH, CONF_THRESHOLD)

# Ergebnisse ausgeben
if not objects:
    print("Keine Objekte erkannt.")
else:
    print(f"Erkannte Objekte ({len(objects)}):")
    for obj in objects:
        print(f"  ID: {obj['id']}, Klasse: {obj['class']}, Konfidenz: {obj['confidence']:.2f}, Box: {obj['box']}")