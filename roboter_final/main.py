import time
import RPi.GPIO as GPIO


from roboter_final import communication
from roboter_final.get_picture import capture_picture_from_api, capture_picture_from_cv2
from roboter_final.YoloDetector import YoloDetector

from roboter_final import lineDetection
import os
from roboter_final.CheckConection import  CheckConnection
from roboter_final.Graph.Graph import Graph
from roboter_final.DegreeInMs import Degree2Milliseconds

START_NODE = "E"
TARGET_NODES = ["A", "B", "C"]
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "my_model.pt")
TXT_PATH = os.path.join(BASE_DIR, "dataset", "detected_objects.txt")
PICTURES = os.path.join(BASE_DIR, "dataset")
FLAGS = []

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



def drive_with_direction(direction: str, has_obstacle: bool ):
        if direction == "links":
            communication.turn_left_to_line(0)

        elif direction == "rechts":
            communication.turn_right_to_line(0)
        elif direction == "mitte":
            print("no turn")
        communication.special_command(0, 50, int(has_obstacle))


def align_with_next_edge(graph:Graph, current_orientation:float):
    edge:str = graph.get_first_edge_in_shortest_path()
    print(f"align with edge{edge}")
    new_orientation: float = graph.edges[edge].get_length_and_angle()[1]
    print(f"current_orientation:{current_orientation}, new_orienation:{new_orientation}")

    difference: float = new_orientation - current_orientation
    print(f"difference:{difference}")
    difference = (difference + 180) % 360 - 180

    difference_in_ms: int = Degree2Milliseconds.turn_degrees_to_ms(difference)
    if abs(difference) < 15:
        print(f"✅ Already aligned {difference} degrees difference – no turn needed")
    elif difference < 0:
        print(f"To much right, turning {-difference} degrees left")
        communication.turn_left(-difference_in_ms)
    elif difference > 0:
        print(f"To much left, turning {difference} degrees right")
        communication.turn_right(difference_in_ms)
    return edge[2], new_orientation




def traverse_graph():
    target_node = communication.read_position()
    graph: Graph = Graph(target_node)
    graph.mirror_y_axis()

    current_orientation: float = 90
    graph.set_current_node(START_NODE)

    # communication.wait_for_start()
    print("🚦 Start empfangen – Traversierung beginnt")

    while graph.current_node != graph.target_node:
        print(graph.current_node)

        next_node, current_orientation = align_with_next_edge(graph, current_orientation)

        print(f"📍 Aktueller Punkt: {graph.current_node}")


        image_path = capture_picture_from_api(os.path.join(PICTURES, f"{graph.current_node.name}.jpg"))

        print(image_path)
        objects = detect_objects(image_path)
        processed_image_path: str = lineDetection.process_image(image_path)
        print(objects)

        check_connection = CheckConnection(processed_image_path, TXT_PATH)
        line_status = check_connection.check_connection()

        print(line_status)
        if line_status == 0:
            print("neues Tages")
            graph.edges[f"{graph.current_node.name}_{next_node}"].set_is_removed(True)

        elif line_status == 1:
            print("fahren, keine wall")
            direction = check_connection.get_turn_direction()
            drive_with_direction(direction, False)
            graph.set_current_node(next_node)


        elif line_status == 2:

            if next_node in FLAGS:
                # Nur Kommunikation setzen, kein Hinzufügen
                print("Fahren mit Wall ist die beste Option")
                direction = check_connection.get_turn_direction()
                drive_with_direction(direction, True)
                graph.set_current_node(next_node)

            else:
                # Wenn der Node nicht drin ist, hinzufügen
                FLAGS.append(next_node)
                graph.edges[f"{graph.current_node.name}_{next_node}"].set_has_obstacle(True)


        elif line_status == 3:
            print("Barrier im Weg")
            graph.nodes[next_node].change_is_blocked()



        if not next_node:
            print("❌ Kein Pfad gefunden. Abbruch.")
            #break
        current_edge:str = f"{graph.current_node.name}_{next_node}"
        print(f"check if {current_edge} has obstacle {graph.edges[current_edge].has_obstacle}")

        #current_node = communication.read_position()
        #print(f"✅ Neue Position: {current_node}")

        time.sleep(1)

    print(f"🎉 Ziel erreicht: {graph.current_node}")
    communication.flash_led(5, 1)

def main():
    try:
        reset_tof()
        traverse_graph()
    finally:
        GPIO.cleanup()
        print("🧹 GPIO aufgeräumt")

if __name__ == "__main__":
    main()