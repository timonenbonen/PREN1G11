from collections import Counter

class PathEditor:
    def __init__(self, filename):
        self.filename = filename
        self.load_paths()

    def load_paths(self):
        with open(self.filename, "r") as f:
            self.paths = [line.strip() for line in f if line.strip()]
        print(f"{len(self.paths)} Wege geladen.")

    def save_paths(self):
        with open(self.filename, "w") as f:
            for path in self.paths:
                f.write(path + "\n")
        print(f"{len(self.paths)} Wege gespeichert.")

    def remove_paths_with_node(self, node):
        node = node.upper()
        before = len(self.paths)
        self.paths = [path for path in self.paths if node not in path.split("->")]
        removed = before - len(self.paths)
        print(f"{removed} Wege mit dem Knoten '{node}' entfernt.")
        self.save_paths()

    def remove_paths_with_connection(self, connection):
        connection = connection.upper().strip()
        before = len(self.paths)
        self.paths = [path for path in self.paths if connection not in path]
        removed = before - len(self.paths)
        print(f"{removed} Wege mit der Verbindung '{connection}' entfernt.")
        self.save_paths()


    def next_best_step(self, current_node):
        current_node = current_node.upper()
        next_nodes = []

        for path in self.paths:
            nodes = path.split("->")
            if current_node in nodes:
                idx = nodes.index(current_node)
                if idx < len(nodes) - 1:
                    next_nodes.append(nodes[idx + 1])

        if not next_nodes:
            print(f"Keine weiteren Schritte von '{current_node}' möglich.")
            return None

        # Zähle wie oft jeder nächste Knoten vorkommt
        counter = Counter(next_nodes)
        best_next = counter.most_common(1)[0]

        print(f"Nächster bester Schritt von '{current_node}' ist '{best_next[0]}' (kommt in {best_next[1]} Wegen vor).")
        return best_next[0]


if __name__ == "__main__":
    editor = PathEditor("wege_von_E_nach_A.txt")

    step = "E"
    while step:
        step = editor.next_best_step(step)

    step = "D"
    while step:
        step = editor.next_best_step(step)

    # Datei, die Klasse 1 vorher erstellt hat:
    filename = "wege_von_A_nach_G.txt"

    # PathEditor laden
    editor = PathEditor(filename)

    # Alle Wege mit dem Knoten 'F' entfernen
    editor.remove_paths_with_node("F")

    # Oder alle Wege mit der Verbindung 'A->B' entfernen
    editor.remove_paths_with_connection("A->B")

