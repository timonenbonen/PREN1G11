import numpy as np

# Die Adjazenzmatrix
adjacency_matrix = np.array([
    # A B C D E F G H
    [0, 1, 0, 0, 0, 1, 0, 1],  # A
    [1, 0, 1, 0, 0, 0, 0, 1],  # B
    [0, 1, 0, 1, 0, 0, 1, 1],  # C
    [0, 0, 1, 0, 1, 0, 1, 0],  # D
    [0, 0, 0, 1, 0, 1, 1, 0],  # E
    [1, 0, 0, 0, 1, 0, 1, 1],  # F
    [0, 0, 1, 1, 1, 1, 0, 1],  # G
    [1, 1, 1, 0, 0, 1, 1, 0]   # H
])

# Knotenbeschriftung
nodes = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
node_to_index = {name: i for i, name in enumerate(nodes)}

# Pfadspeicher
all_paths = []

# Tiefensuche
def dfs(current, target, visited, path):
    visited[current] = True
    path.append(current)

    if current == target:
        all_paths.append(list(path))
    else:
        for neighbor, connected in enumerate(adjacency_matrix[current]):
            if connected and not visited[neighbor]:
                dfs(neighbor, target, visited, path)

    path.pop()
    visited[current] = False

# Benutzereingabe
start_node = input("Startknoten (A-H): ").strip().upper()
end_node = input("Zielknoten (A-H): ").strip().upper()

# Gültigkeit prüfen
if start_node not in node_to_index or end_node not in node_to_index:
    print("Ungültiger Knotenname. Bitte nur A bis H verwenden.")
else:
    start_index = node_to_index[start_node]
    end_index = node_to_index[end_node]

    # Pfade suchen
    dfs(start_index, end_index, [False] * len(nodes), [])

    # Ergebnis schreiben
    with open("wege_von_{}_nach_{}.txt".format(start_node, end_node), "w") as f:
        for path in all_paths:
            path_str = "->".join([nodes[i] for i in path])
            f.write(path_str + "\n")

    print(f"{len(all_paths)} Wege von {start_node} nach {end_node} wurden in 'wege_von_{start_node}_nach_{end_node}.txt' geschrieben.")
