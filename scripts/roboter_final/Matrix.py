from ErkannteObjekte import Objekt
import os
import re
import cv2

def build_matrix_from_detection(txt_file_path: str, image_path: str) -> dict:
    """
    Lädt die erkannte Objektliste (aus .txt) und Bild,
    ordnet Punkte zu, erstellt Adjazenzmatrix und prüft auf Walls.
    Gibt die finale Matrix zurück.
    """

    # Objekte aus TXT laden
    with open(txt_file_path, 'r', encoding='utf-8') as f:
        txt_content = f.read()
    objekte = Objekt.parse_text_to_objects(txt_content)

    # Buchstabe aus Dateiname extrahieren (z. B. test_G.jpg → G)
    match = re.search(r'_([A-Ha-h])(?:/.|_|\b)', os.path.basename(image_path))
    buchstabe = match.group(1).upper() if match else None
    if not buchstabe:
       raise ValueError("Konnte Buchstaben aus Bildnamen nicht extrahieren.")

    # Zuweisung durchführen (z. B. assignment_G)
    assignment_func = getattr(Objekt, f'assignment_{buchstabe}', None)
    if assignment_func is None:
        raise ValueError(f" Keine Assignment-Methode für Punkt {buchstabe} gefunden.")

    if assignment_func.__name__ in ['assignment_G', 'assignment_F']:
        image = cv2.imread(image_path)
        height, width = image.shape[:2]
        assignment_func(objekte, width, height)
    else:
        Objekt.set_current_image_context(objekte, image_path)
        assignment_func(objekte)

    # Matrix berechnen (Linien + Walls)
    matrix, matrix_buchstaben = Objekt.create_adjacency_matrix(objekte, image_path)
    Objekt.find_wall(objekte, matrix, matrix_buchstaben)

    return matrix
