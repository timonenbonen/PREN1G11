import time
import RPi.GPIO as GPIO
import heapq
import communication
from get_picture import capture_picture_from_api
from YoloDetector import YoloDetector
import Matrix
import lineDetection
import os

START_NODE = "E"
TARGET_NODES = ["A", "B", "C"]
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "my_model.pt")
TXT_PATH = os.path.join(BASE_DIR, "dataset", "detected_objects.txt")
PICTURES = os.path.join(BASE_DIR, "pictures")

def reset_tof():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(7, GPIO.OUT)
    for _ in range(2):
        GPIO.output(7, GPIO.LOW)
        time.sleep(1)
        GPIO.output(7, GPIO.HIGH)
        time.sleep(1)


def detect_objects(image_path: str):
    detector = YoloDetector(MODEL_PATH)
    print(detector)
    objects = detector.detect_and_save(image_path=image_path,save_path=TXT_PATH)
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



def traverse_graph():

    current_node = START_NODE
    # communication.wait_for_start()
    print("🚦 Start empfangen – Traversierung beginnt")

    while current_node not in TARGET_NODES:
        print(f"📍 Aktueller Punkt: {current_node}")

        image_path = capture_picture_from_api(f"{PICTURES}_{current_node}.jpg")
        print(image_path)

        objects = detect_objects(image_path)
        processed_image_path: str = lineDetection.process_image(image_path)
        print(objects)

        matrix = Matrix.build_matrix_from_detection(TXT_PATH, processed_image_path)
        print(matrix)
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
        reset_tof()
        traverse_graph()
    finally:
        GPIO.cleanup()
        print("🧹 GPIO aufgeräumt")
