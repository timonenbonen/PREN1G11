import networkx as nx
import matplotlib.pyplot as plt
import numpy as np

# Adjazenzmatrix aus dem bereitgestellten Bild
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

# Knoten-Labels
labels = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']

# Erstelle einen Graphen aus der Adjazenzmatrix
G = nx.Graph(adjacency_matrix)

# Positionierung der Knoten, um das Sechseck mit zwei Mittelpunkten zu visualisieren
pos = {
    0: (-1, 1),  # A
    1: (0, 2),  # B
    2: (1, 1),  # C
    3: (1, -1),  # D
    4: (0, -2),  # E
    5: (-1, -1),  # F
    6: (0, -0.5),  # G
    7: (0, 0.5)  # H
}

# Zeichne den Graphen
plt.figure(figsize=(10, 8))
nx.draw(G, pos, with_labels=True, labels={i: labels[i] for i in range(8)},
        node_size=500, node_color='black', font_color='white',
        font_weight='bold', width=1.5, edge_color='gray')

plt.title("Muster mit Adjazenzmatrix")
plt.axis('off')
plt.show()


# Funktion zur Mustererkennung (prüft, ob ein gegebener Graph dem Muster entspricht)
def check_pattern(test_graph):
    # Implementierung der Mustererkennung
    # 1. Prüfen, ob der Graph 8 Knoten hat
    # 2. Prüfen, ob die Verbindungen dem vorgegebenen Muster entsprechen
    # 3. Erlauben, dass einige Verbindungen fehlen können

    # Hier würde die eigentliche Implementierung folgen
    pass