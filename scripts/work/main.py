import time

import heapq
from YoloDetector import YoloDetector
import Matrix

START_NODE = "E"
TARGET_NODES = ["A", "B", "C"]
MODEL_PATH = "my_model.pt"
TXT_PATH = "C:/Users/timon/hslu/4sem/Pren1/PREN1G11/scripts/work/pictures/detected_objects.txt"
TEST_PICTURES = "C:/Users/timon/hslu/4sem/Pren1/PREN1G11/scripts/work/pictures/"
BILDPFAD = "C:/Users/timon/hslu/4sem/Pren1/PREN1G11/scripts/work/new_pictures/"

def detect_objects(image_path: str):
    detector = YoloDetector(MODEL_PATH)
    print(detector)
    objects = detector.detect_and_save(image_path)
    print(objects)
    detector.save_to_txt(objects, TXT_PATH)
    return objects


def dijkstra_shortest_path(matrix: dict, start: str, targets: list) -> list:
    visited = set()
    heap = [(0, start, [start])]

    while heap:
        cost, node, path = heapq.heappop(heap)
        if node in visited:
            continue
        visited.add(node)

        if node in targets:
            return path

        for neighbor in matrix.get(node, []):
            if neighbor not in visited:
                heapq.heappush(heap, (cost + 1, neighbor, path + [neighbor]))

    return []  # Kein Pfad gefunden


def calculate_next_node(matrix, current_node, target_nodes):
    path = dijkstra_shortest_path(matrix, current_node, target_nodes)
    if len(path) >= 2:
        return path[1]  # nächster Schritt
    return None
import cv2
import numpy as np
import os


def remove_color(img: np.ndarray,
                 bgr_color: tuple,
                 tol: int,
                 bright_thresh: int) -> np.ndarray:
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, bright_mask = cv2.threshold(gray, bright_thresh, 255, cv2.THRESH_BINARY)

    low = np.array([max(c - tol, 0) for c in bgr_color], dtype=np.uint8)
    high = np.array([min(c + tol, 255) for c in bgr_color], dtype=np.uint8)
    color_mask = cv2.inRange(img, low, high)

    combined = cv2.bitwise_or(color_mask, cv2.bitwise_not(bright_mask))

    out = img.copy()
    out[combined != 0] = (255, 255, 255)
    return out


def process_image(input_path: str,
                  bgr_color=(128, 64, 0),
                  tol=100,
                  bright=178):
    if not os.path.isfile(input_path):
        print(f"❌ Datei nicht gefunden: {input_path}")
        return

    img = cv2.imread(input_path)
    if img is None:
        print("❌ Fehler beim Einlesen des Bildes!")
        return

    result = remove_color(img, bgr_color, tol, bright)

    input_dir, input_file = os.path.split(input_path)
    name, _ = os.path.splitext(input_file)
    output_path = os.path.join(input_dir, f"bearbeitet_{name}.jpg")

    if cv2.imwrite(output_path, result):
        print(f"✔ Ergebnis gespeichert unter: {output_path}")
    else:
        print("❌ Fehler beim Speichern!")

def blub():
    picture: str = ("test1.jpg")
    test_picture_path: str = f"{TEST_PICTURES}{picture}"
    objects = detect_objects(test_picture_path)
    print(objects)

    farbe_bgr = (128, 64, 0)             # Ziel-BGR-Farbe
    toleranz = 100                       # Toleranz
    helligkeitsschwelle = 178           # Schwellenwert für Helligkeit

    process_image(
        input_path=test_picture_path,
        bgr_color=farbe_bgr,
        tol=toleranz,
        bright=helligkeitsschwelle
    )

def traverse_graph():

    current_node = START_NODE
    # communication.wait_for_start()
    print("🚦 Start empfangen – Traversierung beginnt")

    while current_node not in TARGET_NODES:
        print(f"📍 Aktueller Punkt: {current_node}")

        image_path = capture_picture_from_api(f"/tmp/Picture_{current_node}.jpg")
        print(image_path)

        objects = detect_objects(image_path)
        print(objects)

        matrix = Matrix.build_matrix_from_detection(TXT_PATH, image_path)
        next_node = calculate_next_node(matrix, current_node, TARGET_NODES)

        if not next_node:
            print("❌ Kein Pfad gefunden. Abbruch.")
            #break
        return None
        command = f"{current_node},{next_node},1000;"
        print(f"➡️ Sende Befehl: {command}")
        communication.send_uart_command(command)

        current_node = communication.read_position()
        print(f"✅ Neue Position: {current_node}")

        time.sleep(1)

    print(f"🎉 Ziel erreicht: {current_node}")


if __name__ == "__main__":
    try:
        #reset_tof()
        #traverse_graph()
        blub()
    finally:
        #GPIO.cleanup()
        print("🧹 GPIO aufgeräumt")
