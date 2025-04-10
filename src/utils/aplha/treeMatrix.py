import os
import sys
import subprocess

import cv2
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
from typing import List, Optional, Tuple, Dict

from src.utils.aplha.ErkannteObjekte import Objekt


class TreeMatrix:
    def __init__(self, dateipfad: str = ""):
        """
        Initialisiert die TreeMatrix mit optionalem Dateipfad.
        """
        self.objekte: List[Objekt] = []
        self.adjacency_matrix: Optional[np.ndarray] = None
        self.matrix_buchstaben: List[str] = []

        if dateipfad:
            self.lade_objekte_aus_datei(dateipfad)

    def _init_adjacency_matrix(self):
        """
        Initialisiert die Adjazenzmatrix mit allen Buchstaben A-H.
        """
        # Verwende alle Buchstaben von A bis H, unabhängig von den vorhandenen Objekten
        all_buchstaben = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']

        # Sammle auch die tatsächlich vorhandenen Buchstaben aus den Objekten
        vorhandene_buchstaben = {obj.buchstabe for obj in self.objekte
                                 if hasattr(obj, 'buchstabe') and obj.buchstabe}

        # Verwende alle Buchstaben von A bis H als Matrix-Indizes
        self.matrix_buchstaben = all_buchstaben

        # Erstelle eine leere Matrix
        n = len(self.matrix_buchstaben)
        self.adjacency_matrix = np.zeros((n, n), dtype=int)

        print(f"Adjacency-Matrix initialisiert mit allen Buchstaben A-H")
        print(f"Aktuell vorhandene Buchstaben: {sorted(vorhandene_buchstaben)}")
    def lade_objekte_aus_datei(self, dateipfad: str) -> bool:
        """
        Lädt Objekte aus einer Datei und gibt Erfolg zurück.
        """
        try:
            with open(dateipfad, 'r') as datei:
                for zeile in datei:
                    if not zeile.strip():
                        continue

                    daten = zeile.strip().split(';')
                    if len(daten) >= 3:
                        klasse = daten[0]
                        vertrauen = float(daten[1].strip('%'))
                        bbox = tuple(map(int, daten[2].strip('()').split(',')))

                        from src.utils.aplha.ErkannteObjekte import Objekt
                        self.objekte.append(Objekt(klasse, vertrauen, bbox))

            print(f"Erfolgreich {len(self.objekte)} Objekte geladen")
            return True

        except Exception as e:
            print(f"Fehler beim Laden: {str(e)}")
            return False

    def draw_points_and_connections(self, input_image_path: str, output_image_path: str,
                                    nur_buchstaben: Optional[List[str]] = None,
                                    title: str = "Objekte und Verbindungen") -> bool:
        try:
            img = cv2.imread(input_image_path)
            if img is None:
                raise FileNotFoundError(f"Bild nicht gefunden: {input_image_path}")

            img_with_objects = img.copy()

            # Nur gewünschte Objekte verwenden (optional einschränken)
            beschriftete_objekte = {
                obj.buchstabe: obj for obj in self.objekte
                if hasattr(obj, 'buchstabe') and obj.buchstabe and
                   (nur_buchstaben is None or obj.buchstabe in nur_buchstaben)
            }

            farben = {
                'A': (255, 0, 0), 'B': (0, 255, 0), 'C': (0, 0, 255),
                'D': (255, 255, 0), 'E': (255, 0, 255), 'F': (0, 255, 255),
                'G': (128, 0, 128), 'H': (0, 128, 128)
            }

            # Kreise und Labels zeichnen
            for buchstabe, obj in beschriftete_objekte.items():
                if hasattr(obj, 'zentrum') and hasattr(obj, 'bounding_box'):
                    try:
                        zentrum = tuple(map(int, obj.zentrum)) if not isinstance(obj.zentrum, tuple) else (
                            int(obj.zentrum[0]), int(obj.zentrum[1]))
                    except (TypeError, AttributeError):
                        continue

                    farbe = farben.get(buchstabe, (255, 255, 255))

                    cv2.circle(img_with_objects, zentrum, 10, farbe, -1)

                    try:
                        x1, y1, x2, y2 = map(int, obj.bounding_box)
                        cv2.rectangle(img_with_objects, (x1, y1), (x2, y2), farbe, 2)
                    except (TypeError, ValueError):
                        continue

                    cv2.putText(img_with_objects, buchstabe,
                                (zentrum[0] - 5, zentrum[1] + 5),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

            # Verbindungen zeichnen (nur innerhalb der gefilterten Buchstaben)
            for i, b1 in enumerate(self.matrix_buchstaben):
                if nur_buchstaben and b1 not in nur_buchstaben:
                    continue
                for j, b2 in enumerate(self.matrix_buchstaben):
                    if i < j and self.adjacency_matrix[i, j] == 1:
                        if nur_buchstaben and (b2 not in nur_buchstaben):
                            continue
                        p1 = beschriftete_objekte.get(b1).zentrum
                        p2 = beschriftete_objekte.get(b2).zentrum
                        if p1 and p2:
                            cv2.line(img_with_objects, tuple(map(int, p1)), tuple(map(int, p2)), (200, 200, 200), 2)

            output_dir = os.path.dirname(output_image_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)

            cv2.imwrite(output_image_path, img_with_objects)
            print(f"Bild mit Objekten und Verbindungen gespeichert unter: {output_image_path}")
            return True

        except Exception as e:
            print(f"Fehler beim Zeichnen: {str(e)}")
            return False

    def erste_zuordnung(self, dateipfad: Optional[str] = None,
                        connection_image_path: Optional[str] = None) -> bool:
        """
        Ordnet E, F, G, D zu und aktualisiert die Matrix für Punkt E.
        """
        if dateipfad and not self.lade_objekte_aus_datei(dateipfad):
            return False

        relevante = [obj for obj in self.objekte
                     if hasattr(obj, 'klasse') and obj.klasse in ['point', 'pointa', 'pointb', 'pointc', 'barrier']
                     and hasattr(obj, 'zentrum')]

        if not relevante:
            print("Keine relevanten Objekte gefunden")
            return False

        # Zuordnung E, F, G, D
        unterster = max(relevante, key=lambda obj: obj.zentrum[1])
        unterster.set_buchstabe('E')

        übrige = [obj for obj in relevante if obj != unterster]
        drei_unterste = sorted(übrige, key=lambda obj: obj.zentrum[1], reverse=True)[:3]
        drei_unterste_sortiert = sorted(drei_unterste, key=lambda obj: obj.zentrum[0])

        for obj, buchstabe in zip(drei_unterste_sortiert, ['F', 'G', 'D']):
            obj.set_buchstabe(buchstabe)

        # Matrix aktualisieren für Punkt E
        if connection_image_path:
            print("\nAktualisiere Adjazenzmatrix für Punkt E...")
            self.create_adjacency_matrix(
                connection_image_path,
                objekte=self.objekte,
                aktueller_punkt='E'
            )

            # Visualisiere den aktuellen Graphen
            self.visualize_current_graph()

            # Zeichne die Objekte und Verbindungen auf das Bild
            dataset_pfad = os.path.dirname(connection_image_path)
            output_image_path = os.path.join(dataset_pfad, "bild1_mit_zuordnung.jpg")
            self.draw_points_and_connections(
                connection_image_path,
                output_image_path,
                "Zuordnung Phase 1: E, F, G, D"
            )

        return True

    def zuordnung_von_punkt_f(self, dateipfad: Optional[str] = None,
                              connection_image_path: Optional[str] = None) -> bool:
        """
        Ordnet A, B, H, G zu von Punkt F aus und aktualisiert alle F-Verbindungen.
        """
        if dateipfad and not self.lade_objekte_aus_datei(dateipfad):
            return False

        relevante = [obj for obj in self.objekte
                     if hasattr(obj, 'klasse') and obj.klasse in ['point', 'pointa', 'pointb', 'pointc', 'barrier']
                     and hasattr(obj, 'zentrum')]

        # Finde oder erstelle Punkt F
        punkt_f = next((obj for obj in relevante if getattr(obj, 'buchstabe', None) == 'F'), None)
        if not punkt_f:
            punkt_f = next((obj for obj in relevante if obj.klasse.lower() == 'pointf'), None)
            if punkt_f:
                punkt_f.set_buchstabe('F')
            else:
                untere = sorted(relevante, key=lambda obj: obj.zentrum[1], reverse=True)[:len(relevante) // 2]
                punkt_f = min(untere, key=lambda obj: obj.zentrum[0])
                punkt_f.set_buchstabe('F')

        # Zuordnung A, B, H, G
        unmarkiert = [obj for obj in relevante if not getattr(obj, 'buchstabe', None)]

        # Punkt A zuweisen
        punkt_a = next((obj for obj in unmarkiert if obj.klasse.lower() == 'pointa'), None)
        if not punkt_a:
            punkt_a = min(unmarkiert, key=lambda obj: obj.zentrum[0])
        punkt_a.set_buchstabe('A')

        # Punkte B, H, G zuweisen basierend auf Nähe zu F
        if punkt_f and hasattr(punkt_f, 'zentrum'):
            f_x, f_y = punkt_f.zentrum
            for obj in unmarkiert:
                if obj != punkt_a:
                    obj.distanz_zu_f = ((obj.zentrum[0] - f_x) ** 2 + (obj.zentrum[1] - f_y) ** 2) ** 0.5

            nahe = sorted([obj for obj in unmarkiert if obj != punkt_a],
                          key=lambda obj: getattr(obj, 'distanz_zu_f', float('inf')))[:3]
            sortiert = sorted(nahe, key=lambda obj: obj.zentrum[1])

            if len(sortiert) > 0:
                sortiert[0].set_buchstabe('B')
            if len(sortiert) > 1:
                sortiert[1].set_buchstabe('H')
            if len(sortiert) > 2:
                sortiert[2].set_buchstabe('G')

        # Matrix aktualisieren für Punkt F
        if connection_image_path:
            print("\nAktualisiere Adjazenzmatrix für Punkt F...")
            self.create_adjacency_matrix(
                connection_image_path,
                objekte=self.objekte,
                aktueller_punkt='F'
            )

            # Jetzt aktualisiere auch die Verbindungen für alle neu zugewiesenen Punkte
            print("\nAktualisiere Adjazenzmatrix für alle neuen Punkte...")
            neue_punkte = ['A', 'B', 'H']
            for punkt in neue_punkte:
                # Prüfe ob der Punkt existiert
                if any(obj.buchstabe == punkt for obj in self.objekte):
                    print(f"Aktualisiere Verbindungen für Punkt {punkt}...")
                    self.create_adjacency_matrix(
                        connection_image_path,
                        objekte=self.objekte,
                        aktueller_punkt=punkt
                    )

            # Visualisiere den aktuellen Graphen
            self.visualize_current_graph()

            # Zeichne die Objekte und Verbindungen auf das Bild
            dataset_pfad = os.path.dirname(connection_image_path)
            output_image_path = os.path.join(dataset_pfad, "bild2_mit_zuordnung.jpg")
            self.draw_points_and_connections(
                connection_image_path,
                output_image_path,
                "Zuordnung Phase 2: A, B, H, G + Verbindungen"
            )

        return True

    def create_adjacency_matrix(self, connection_image_path: str,
                                objekte: List[Objekt] = None,
                                aktueller_punkt: Optional[str] = None,
                                threshold: float = 0.15,
                                bar_width: int = 10) -> Tuple[np.ndarray, List[str]]:
        """
        Aktualisiert die Adjazenzmatrix für einen spezifischen Punkt basierend auf Verbindungen im Bild.

        Args:
            connection_image_path: Pfad zum Bild mit den Verbindungen
            objekte: Liste der Objekte zum Prüfen (optional, sonst werden gespeicherte verwendet)
            aktueller_punkt: Buchstabe des Punktes, dessen Verbindungen aktualisiert werden sollen
            threshold: Schwellenwert für die Verbindungserkennung
            bar_width: Breite des Bereichs zum Prüfen der Verbindung

        Returns:
            Tuple aus aktualisierter Adjazenzmatrix und Liste der Buchstaben
        """
        # Original-Matrix für Vergleich
        original_matrix = np.array([
            # A B C D E F G H
            [0, 1, 0, 0, 0, 1, 0, 1],  # A
            [1, 0, 1, 0, 0, 0, 0, 1],  # B
            [0, 1, 0, 1, 0, 0, 1, 1],  # C
            [0, 0, 1, 0, 1, 0, 1, 0],  # D
            [0, 0, 0, 1, 0, 1, 1, 0],  # E
            [1, 0, 0, 0, 1, 0, 1, 1],  # F
            [0, 0, 1, 1, 1, 1, 0, 1],  # G
            [1, 1, 1, 0, 0, 1, 1, 0]  # H
        ])

        # Original-Buchstaben für Zuordnung
        original_buchstaben = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']

        # Wenn keine Objekte übergeben wurden, verwende die eigenen
        if objekte is None:
            objekte = self.objekte

        if not hasattr(self, 'adjacency_matrix') or self.adjacency_matrix is None:
            self._init_adjacency_matrix()

        # Erstelle Dictionary mit Buchstaben als Schlüssel und Objekten als Werte
        punkt_dict = {obj.buchstabe: obj for obj in objekte
                      if hasattr(obj, 'buchstabe') and obj.buchstabe in self.matrix_buchstaben}

        try:
            img = cv2.imread(connection_image_path)
            if img is None:
                raise FileNotFoundError(f"Bild nicht gefunden: {connection_image_path}")
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            if aktueller_punkt and aktueller_punkt in punkt_dict and aktueller_punkt in self.matrix_buchstaben:
                b1 = aktueller_punkt
                i = self.matrix_buchstaben.index(b1)
                p1 = punkt_dict[b1].zentrum

                # Finde die Position in der Original-Matrix
                orig_i = original_buchstaben.index(b1) if b1 in original_buchstaben else -1

                # Prüfe alle möglichen Verbindungen vom aktuellen Punkt
                for b2 in self.matrix_buchstaben:
                    if b2 != b1 and b2 in punkt_dict:
                        j = self.matrix_buchstaben.index(b2)
                        p2 = punkt_dict[b2].zentrum

                        # Prüfe, ob diese Verbindung in der Original-Matrix existiert
                        orig_j = original_buchstaben.index(b2) if b2 in original_buchstaben else -1
                        allowed_connection = False

                        if orig_i >= 0 and orig_j >= 0:
                            allowed_connection = original_matrix[orig_i, orig_j] == 1

                        if allowed_connection:
                            # Prüfe die tatsächliche Verbindung im Bild
                            connected = self._prüfe_verbindung(gray, p1, p2, threshold, bar_width)
                            self.adjacency_matrix[i, j] = connected
                            self.adjacency_matrix[j, i] = connected  # Matrix ist symmetrisch
                        else:
                            # Wenn laut Original keine Verbindung besteht, kann auch keine erkannt werden
                            self.adjacency_matrix[i, j] = 0
                            self.adjacency_matrix[j, i] = 0

                # Debug-Ausgabe
                print(f"Verbindungen für {b1} aktualisiert")
                verbindungen = [self.matrix_buchstaben[j] for j, val in enumerate(self.adjacency_matrix[i]) if val == 1]
                print(f"{b1} ist verbunden mit: {', '.join(verbindungen)}")

            elif aktueller_punkt:
                print(f"Warnung: Punkt '{aktueller_punkt}' nicht in Punkt-Dictionary oder Matrix-Buchstaben gefunden.")
            else:
                print("Warnung: Kein spezifischer Punkt zum Überprüfen angegeben.")

        except Exception as e:
            print(f"Matrix Fehler: {str(e)}")
            import traceback
            traceback.print_exc()

        return self.adjacency_matrix, self.matrix_buchstaben

    def _prüfe_verbindung(self, gray_img: np.ndarray, p1: Tuple[int, int],
                          p2: Tuple[int, int], threshold: float = 0.10,
                          bar_width: int = 10) -> bool:
        """
        Prüft ob zwei Punkte verbunden sind.
        """
        dx, dy = p2[0] - p1[0], p2[1] - p1[1]
        length = max(1, int(np.sqrt(dx * dx + dy * dy)))

        if length == 0:
            return False

        nx, ny = -dy / length, dx / length
        non_white = 0
        total = 0

        for t in range(length):
            x = int(p1[0] + t * dx / length)
            y = int(p1[1] + t * dy / length)
            for w in range(-bar_width // 2, bar_width // 2 + 1):
                wx, wy = int(x + w * nx), int(y + w * ny)
                if 0 <= wx < gray_img.shape[1] and 0 <= wy < gray_img.shape[0]:
                    total += 1
                    if gray_img[wy, wx] < 245:
                        non_white += 1

        return (non_white / total) >= threshold if total > 0 else False

    def visualize_current_graph(self, output_path: str = "graph_visualisierung.png") -> bool:
        """
        Visualisiert den aktuellen Graphen basierend auf der Adjazenzmatrix.
        """
        try:
            if not hasattr(self, 'adjacency_matrix') or self.adjacency_matrix is None:
                print("Keine Daten zur Visualisierung")
                return False

            output_dir = os.path.dirname(output_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)

            # Erstelle neuen Graphen
            G = nx.Graph()

            # Füge alle Buchstaben als Knoten hinzu, unabhängig von Verbindungen
            G.add_nodes_from(self.matrix_buchstaben)

            # Füge Kanten basierend auf der Adjazenzmatrix hinzu
            for i in range(len(self.matrix_buchstaben)):
                for j in range(i + 1,
                               len(self.matrix_buchstaben)):  # nur oberes Dreieck verwenden (Matrix ist symmetrisch)
                    if self.adjacency_matrix[i, j] == 1:
                        G.add_edge(self.matrix_buchstaben[i], self.matrix_buchstaben[j])

            # Feste Positionen für die Knoten (geometrisch logisch angeordnet)
            pos = {
                'A': (-1, 1), 'B': (0, 1.5), 'C': (1, 1),
                'D': (1, -1), 'E': (0, -1.5), 'F': (-1, -1),
                'G': (0, -0.5), 'H': (0, 0.5)
            }
            # Nur Knoten positionieren, die im Graphen vorhanden sind
            pos = {k: v for k, v in pos.items() if k in self.matrix_buchstaben}

            # Erzeuge Farben basierend auf Existenz des Punktes
            node_colors = []
            for buchstabe in self.matrix_buchstaben:
                exists = any(hasattr(obj, 'buchstabe') and obj.buchstabe == buchstabe for obj in self.objekte)
                node_colors.append('skyblue' if exists else 'lightgray')

            # Debug Ausgabe
            print(f"\nVisualisiere Graph mit {len(G.nodes())} Knoten und {len(G.edges())} Kanten")
            print(f"Knoten: {list(G.nodes())}")
            print(f"Kanten: {list(G.edges())}")

            # Zeichne den Graphen
            plt.figure(figsize=(10, 8))
            nx.draw(G, pos,
                    nodelist=self.matrix_buchstaben,  # Verwende die originale Reihenfolge
                    node_color=node_colors,
                    with_labels=True,
                    node_size=700,
                    font_size=12,
                    font_weight='bold')

            # Graph-Titel
            plt.title("Baumstruktur Visualisierung (aktueller Status)")

            # Speichere den Graphen
            plt.savefig(output_path)
            plt.close()

            print(f"Graph wurde erfolgreich unter {output_path} gespeichert")
            return True

        except Exception as e:
            print(f"Visualisierungsfehler: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    def print_adjacency_matrix(self):
        """Gibt die Adjazenzmatrix aus."""
        if not hasattr(self, 'adjacency_matrix') or self.adjacency_matrix is None:
            print("Matrix nicht initialisiert")
            return

        print("\nAdjazenzmatrix:")
        print("   " + " ".join(self.matrix_buchstaben))
        for i, row in enumerate(self.adjacency_matrix):
            print(f"{self.matrix_buchstaben[i]} {list(row)}")

    def objekte_in_datei_speichern(self, zieldatei: str = "objekte_beschriftet.txt") -> bool:
        """Speichert die Objekte in eine Datei."""
        try:
            with open(zieldatei, 'w') as f:
                for obj in self.objekte:
                    line = f"{obj.klasse};{obj.vertrauen:.1f}%;{obj.bounding_box};"
                    line += f"{getattr(obj, 'flaeche', '')};{getattr(obj, 'zentrum', '')};"
                    line += f"{getattr(obj, 'buchstabe', '')}\n"
                    f.write(line)
            return True
        except Exception as e:
            print(f"Speicherfehler: {str(e)}")
            return False


def main():
    """
    Hauptfunktion mit verbessertem Fehlerhandling, Pfadmanagement und Matrix-Updates
    """
    # Pfade mit os.path.join für plattformübergreifende Kompatibilität
    dataset_pfad = os.path.abspath("Dataset")

    # Eingabedateien
    objekte1_datei = os.path.join(dataset_pfad, "objekte1.txt")
    bild1_datei = os.path.join(dataset_pfad, "bild1.jpg")
    objekte2_datei = os.path.join(dataset_pfad, "objekte2.txt")
    bild2_datei = os.path.join(dataset_pfad, "bild2.jpg")

    # Ausgabedateien
    objekte_beschriftet_datei = os.path.join(dataset_pfad, "objekte_beschriftet.txt")
    graph_visualisierung_datei = os.path.join(dataset_pfad, "graph_visualisierung.png")
    final_image_path = os.path.join(dataset_pfad, "finale_visualisierung.jpg")

    try:
        # Sicherstellen, dass der Dataset-Ordner existiert
        os.makedirs(dataset_pfad, exist_ok=True)

        # 1. Initialisierung
        print("Initialisiere TreeMatrix...")
        matrix = TreeMatrix("")  # Leere Initialisierung

        # 2. Phase 1: Grundzuordnung mit Punkt E als Fokus
        print("\n=== PHASE 1: Grundzuordnung mit Fokus auf Punkt E ===")
        if not os.path.exists(objekte1_datei):
            raise FileNotFoundError(f"Objektdaten nicht gefunden: {objekte1_datei}")
        if not os.path.exists(bild1_datei):
            raise FileNotFoundError(f"Bilddatei nicht gefunden: {bild1_datei}")

        erfolg1 = matrix.erste_zuordnung(objekte1_datei, bild1_datei)
        if erfolg1:
            print("Grundzuordnung erfolgreich abgeschlossen.")
            print("Matrix für Punkt E wurde aktualisiert.")
            matrix.print_adjacency_matrix()
        else:
            print("Warnung: Grundzuordnung konnte nicht vollständig durchgeführt werden.")

        # 3. Phase 2: Erweiterte Zuordnung mit Punkt F als Fokus
        print("\n=== PHASE 2: Erweiterte Zuordnung mit Fokus auf Punkt F ===")
        if not os.path.exists(objekte2_datei):
            raise FileNotFoundError(f"Objektdaten nicht gefunden: {objekte2_datei}")
        if not os.path.exists(bild2_datei):
            raise FileNotFoundError(f"Bilddatei nicht gefunden: {bild2_datei}")

        erfolg2 = matrix.zuordnung_von_punkt_f(objekte2_datei, bild2_datei)
        if erfolg2:
            print("Erweiterte Zuordnung erfolgreich abgeschlossen.")
            print("Matrix für Punkt F und neue Punkte wurde aktualisiert.")
            matrix.print_adjacency_matrix()
        else:
            print("Warnung: Erweiterte Zuordnung konnte nicht vollständig durchgeführt werden.")

        # 4. Finale Ausgaben
        print("\n=== ERGEBNISSE ===")
        # Adjazenzmatrix
        print("\nFinale Adjazenzmatrix:")
        matrix.print_adjacency_matrix()

        # Visualisierung
        print(f"\nGeneriere finale Graphvisualisierung...")
        try:
            if matrix.visualize_current_graph(graph_visualisierung_datei):
                print(f"Visualisierung gespeichert unter: {graph_visualisierung_datei}")
            else:
                print("Warnung: Visualisierung fehlgeschlagen")

            # Erstelle eine finale Visualisierung auf dem zweiten Bild mit allen Punkten und Verbindungen
            if matrix.draw_points_and_connections(bild2_datei, final_image_path, "Finale Zuordnung aller Punkte"):
                print(f"Finale Bildvisualisierung gespeichert unter: {final_image_path}")
            else:
                print("Warnung: Finale Bildvisualisierung fehlgeschlagen")
        except Exception as e:
            print(f"Fehler bei Visualisierung: {str(e)}")

        # Daten speichern
        print(f"\nSpeichere beschriftete Objekte...")
        if matrix.objekte_in_datei_speichern(objekte_beschriftet_datei):
            print(f"Daten erfolgreich gespeichert unter: {objekte_beschriftet_datei}")
        else:
            print("Fehler beim Speichern der Objektdaten!")

        print("\nVerarbeitung erfolgreich abgeschlossen!")
        return 0

    except FileNotFoundError as e:
        print(f"\nFEHLER: Datei nicht gefunden - {e}")
        print("Bitte überprüfen Sie folgende Pfade:")
        print(f"- Dataset-Verzeichnis: {dataset_pfad}")
        print(f"- Objektdateien: {objekte1_datei}, {objekte2_datei}")
        print(f"- Bilddateien: {bild1_datei}, {bild2_datei}")
        return 1

    except Exception as e:
        print(f"\nKRITISCHER FEHLER: {str(e)}")
        import traceback
        traceback.print_exc()
        return 2


if __name__ == "__main__":
    main()