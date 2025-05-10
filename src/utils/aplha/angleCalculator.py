import tkinter as tk
import numpy as np
import itertools

adjacency_matrix = np.array([
    [0, 1, 0, 0, 0, 1, 0, 1],
    [1, 0, 1, 0, 0, 0, 0, 1],
    [0, 1, 0, 1, 0, 0, 1, 1],
    [0, 0, 1, 0, 1, 0, 1, 0],
    [0, 0, 0, 1, 0, 1, 1, 0],
    [1, 0, 0, 0, 1, 0, 1, 1],
    [0, 0, 1, 1, 1, 1, 0, 1],
    [1, 1, 1, 0, 0, 1, 1, 0]
])
labels = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']

positions = {
    0: [100, 100],
    1: [200, 50],
    2: [300, 100],
    3: [300, 200],
    4: [200, 300],
    5: [100, 200],
    6: [200, 200],
    7: [200, 125]
}

class GraphApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Alle Winkel in allen Dreiecken")
        self.canvas = tk.Canvas(root, width=600, height=400, bg='white')
        self.canvas.pack()

        self.nodes = {}
        self.dragging = None

        self.draw_graph()
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonPress-1>", self.on_click)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

    def draw_graph(self):
        self.canvas.delete("all")

        # Kanten
        for i in range(len(adjacency_matrix)):
            for j in range(i + 1, len(adjacency_matrix)):
                if adjacency_matrix[i, j]:
                    x1, y1 = positions[i]
                    x2, y2 = positions[j]
                    self.canvas.create_line(x1, y1, x2, y2, fill="black")

        # Dreiecke
        triangles = self.find_triangles()
        angle_offset_map = {}  # Offset zur besseren Lesbarkeit

        for tri in triangles:
            a, b, c = tri

            # Berechne Winkel bei jedem Eckpunkt
            angles = [
                (a, self.calculate_angle(positions[b], positions[a], positions[c])),
                (b, self.calculate_angle(positions[a], positions[b], positions[c])),
                (c, self.calculate_angle(positions[a], positions[c], positions[b]))
            ]

            for idx, angle in angles:
                # Position des Eckpunkts
                px, py = positions[idx]

                # Die anderen zwei Punkte im Dreieck
                others = [p for p in tri if p != idx]
                p1 = np.array(positions[others[0]])
                p2 = np.array(positions[others[1]])
                p = np.array([px, py])

                # Vektoren zu den anderen Punkten
                v1 = (p1 - p) / np.linalg.norm(p1 - p)
                v2 = (p2 - p) / np.linalg.norm(p2 - p)

                # Richtung entlang der Winkelhalbierenden
                bisector = (v1 + v2)
                if np.linalg.norm(bisector) == 0:
                    bisector = np.array([0, 0])
                else:
                    bisector = bisector / np.linalg.norm(bisector)

                # Position etwas entlang der Winkelhalbierenden
                offset_length = 20
                tx, ty = p + bisector * offset_length

                self.canvas.create_text(tx, ty, text=f"{angle:.1f}°", fill="red", font=("Arial", 8))

        # Knoten
        self.nodes.clear()
        for i, (x, y) in positions.items():
            r = 10
            oval = self.canvas.create_oval(x - r, y - r, x + r, y + r, fill="skyblue")
            label = self.canvas.create_text(x, y, text=labels[i], font=("Arial", 10, "bold"))
            self.nodes[oval] = i
            self.nodes[label] = i

    def get_offset_vector(self, index):
        # Gibt versetzte Position für Mehrfachwinkel an einem Knoten
        angle = index * 40
        radius = 15
        rad = np.radians(angle)
        return radius * np.cos(rad), radius * np.sin(rad)

    def find_triangles(self):
        triangles = set()
        for i in range(len(adjacency_matrix)):
            neighbors = [j for j in range(len(adjacency_matrix)) if adjacency_matrix[i][j]]
            for j, k in itertools.combinations(neighbors, 2):
                if adjacency_matrix[j][k]:
                    triangles.add(tuple(sorted((i, j, k))))
        return list(triangles)

    def calculate_angle(self, p1, p2, p3):
        a = np.array(p1)
        b = np.array(p2)
        c = np.array(p3)
        ba = a - b
        bc = c - b
        cosine = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
        angle = np.arccos(np.clip(cosine, -1.0, 1.0))
        return np.degrees(angle)

    def on_click(self, event):
        for item in self.nodes:
            x, y = positions[self.nodes[item]]
            if (event.x - x)**2 + (event.y - y)**2 <= 100:
                self.dragging = self.nodes[item]
                break

    def on_drag(self, event):
        if self.dragging is not None:
            positions[self.dragging] = [event.x, event.y]
            self.draw_graph()

    def on_release(self, event):
        self.dragging = None

# Starten
root = tk.Tk()
app = GraphApp(root)
root.mainloop()
