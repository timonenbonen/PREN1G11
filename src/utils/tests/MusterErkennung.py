import cv2
import numpy as np
import mediapipe as mp  # Korrekter Import
import networkx as nx
import matplotlib.pyplot as plt

# Mediapipe Initialisierung
mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose


def detect_points_and_edges(image_path):
    # Bild laden
    img = cv2.imread(image_path)
    if img is None:
        print("Fehler: Bild konnte nicht geladen werden!")
        return [], []

    # Bild in Graustufen umwandeln
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Bild vorverarbeiten
    blurred = cv2.GaussianBlur(gray, (9, 9), 2)  # Rauschen reduzieren
    _, threshold = cv2.threshold(blurred, 200, 255, cv2.THRESH_BINARY)  # Schwelle anwenden

    # Hough-Kreistransformation anwenden
    circles = cv2.HoughCircles(
        threshold,
        cv2.HOUGH_GRADIENT,
        dp=1,              # Auflösungsfaktor
        minDist=20,        # Mindestabstand zwischen den Kreismittelpunkten
        param1=50,         # Obere Schwelle für die Canny-Kantenerkennung
        param2=25,         # Schwelle für die Kreiserkennung (je kleiner, desto mehr Kreise)
        minRadius=10,      # Minimale Kreisgröße
        maxRadius=100      # Maximale Kreisgröße
    )

    # Überprüfe, ob Kreise erkannt wurden
    if circles is None:
        print("Keine Kreise erkannt!")
        return [], []

    # Extrahiere die Mittelpunkte der Kreise
    circles = np.uint16(np.around(circles))
    points = [(circle[0], circle[1]) for circle in circles[0, :]]  # Mittelpunkte als Punkte

    print("Gefundene Punkte:", points)

    # Kanten mittels Adjazenzmatrix erkennen
    adjacency_matrix = np.array([
        [0, 1, 0, 0, 0, 1, 0, 1],  # A
        [1, 0, 1, 0, 0, 0, 0, 1],  # B
        [0, 1, 0, 1, 0, 0, 1, 1],  # C
        [0, 0, 1, 0, 1, 0, 1, 0],  # D
        [0, 0, 0, 1, 0, 1, 1, 0],  # E
        [1, 0, 0, 0, 1, 0, 1, 1],  # F
        [0, 0, 1, 1, 1, 1, 0, 1],  # G
        [1, 1, 1, 0, 0, 1, 1, 0]  # H
    ])

    edges = []
    for i in range(len(points)):
        for j in range(len(points)):
            if adjacency_matrix[i, j] == 1:
                edges.append((i, j))

    return points, edges


def draw_graph(points, edges):
    G = nx.Graph()

    for i, point in enumerate(points):
        G.add_node(i, pos=point)

    G.add_edges_from(edges)

    pos = nx.get_node_attributes(G, 'pos')
    plt.figure(figsize=(8, 6))
    nx.draw(G, pos, with_labels=True, node_size=500, node_color='black', font_color='white')
    plt.show()


# Beispiel-Aufruf
image_path = r"C:\Users\marin\PycharmProjects\PREN1G11\src\utils\tests\Bilder\MusterBoden\boden1.jpg"
points, edges = detect_points_and_edges(image_path)
draw_graph(points, edges)