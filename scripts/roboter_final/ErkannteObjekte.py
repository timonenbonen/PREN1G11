from sympy.strategies.core import switch


class Objekt:
    def __init__(self, klasse, vertrauen, bounding_box):
        self.klasse = klasse
        self.vertrauen = vertrauen
        self.bounding_box = bounding_box
        self.flaeche = self._area()
        self.zentrum = self._center()
        self.buchstabe = None

        if self.klasse in ['pointa', 'pointb', 'pointc']:
            self._assign_letter()

    def _area(self):
        x1, y1, x2, y2 = self.bounding_box
        return (x2 - x1) * (y2 - y1)

    def _center(self):
        x1, y1, x2, y2 = self.bounding_box
        if self.klasse == 'barrier':
            return ((x1 + x2) / 2, y2 - ((x2 - x1) / 2))
        return ((x1 + x2) / 2, (y1 + y2) / 2)

    def _assign_letter(self):
        mapping = {'pointa': 'A', 'pointb': 'B', 'pointc': 'C'}
        self.buchstabe = mapping.get(self.klasse)

    @staticmethod
    def parse_text_to_objects(txt_content: str) -> list:
        objects = []
        lines = txt_content.strip().splitlines()
        for line in lines:
            parts = line.split(";")
            if len(parts) < 5:
                continue
            klasse = parts[0]
            vertrauen = float(parts[1].replace("%", ""))
            bbox = eval(parts[2])
            obj = Objekt(klasse, vertrauen, bbox)
            obj.flaeche = float(parts[3])
            obj.zentrum = eval(parts[4])
            if len(parts) > 5 and parts[5]:
                obj.buchstabe = parts[5]
            objects.append(obj)
        return objects

    @staticmethod
    def assignment_A(objects: list):
        letter = ord("A")
        for obj in sorted(objects, key=lambda o: o.zentrum[0]):
            obj.buchstabe = chr(letter)
            letter += 1

    @staticmethod
    def create_adjacency_matrix(objects: list, image_path: str):
        matrix = {}
        obj_letters = [obj.buchstabe for obj in objects if obj.buchstabe]
        for i in range(len(obj_letters) - 1):
            a, b = obj_letters[i], obj_letters[i + 1]
            matrix.setdefault(a, []).append(b)
            matrix.setdefault(b, []).append(a)
        return matrix, obj_letters

    @staticmethod
    def find_wall(objects: list, matrix: dict, obj_letters: list):
        print("🚧 Wall-Erkennung übersprungen (Dummy-Modus).")
