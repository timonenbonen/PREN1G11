import numpy as np





def next_step(adjacency_matrix, current_node, goal_nodes):
    """
    Gibt den nächsten Knoten zurück, der auf kürzestem Weg zu einem Zielknoten führt.
    Wird bei jedem Schritt erneut mit aktualisierter Matrix aufgerufen.
    """
    from collections import deque

    visited = set()
    queue = deque([[current_node]])

    while queue:
        path = queue.popleft()
        node = path[-1]

        if node in goal_nodes and node != current_node:
            return path[1]  # Gib den nächsten Schritt zurück

        if node not in visited:
            visited.add(node)
            neighbors = np.where(adjacency_matrix[node] == 1)[0]
            for neighbor in neighbors:
                if neighbor not in path:
                    new_path = list(path)
                    new_path.append(neighbor)
                    queue.append(new_path)

    return None  # Kein erreichbares Ziel

# Beispiel-Aufruf pro Schritt:
# Startpunkt
current_position = 4  # E
goals = [0, 1, 2]  # A, B, C

# Nehmen wir an, du aktualisierst `adjacency_matrix` nach jedem Schritt:
next_pos = next_step(adjacency_matrix, current_position, goals)

if next_pos is not None:
    print(f"Weitergehen zu: {chr(ord('A') + next_pos)}")
    # Jetzt Bild an next_pos machen, Matrix aktualisieren, und erneut aufrufen
else:
    print("Kein erreichbarer Weg aktuell.")
