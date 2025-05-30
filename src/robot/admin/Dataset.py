import os
import shutil
from typing import Tuple

class DatasetSample:
    def __init__(self, folder: str):
        self.folder = folder

    @property
    def original_image(self):
        return self._find_file(prefix='original_')

    @property
    def edited_image(self):
        return self._find_file(prefix='edited_')

    @property
    def textfile(self):
        return self._find_file(suffix='.txt')

    def _find_file(self, prefix=None, suffix=None):
        for f in os.listdir(self.folder):
            if prefix and f.startswith(prefix):
                return os.path.join(self.folder, f)
            if suffix and f.endswith(suffix):
                return os.path.join(self.folder, f)
        return None

class Dataset:
    def __init__(self, base_dir: str):
        self.base_dir = os.path.abspath(base_dir)
        print(f"Dataset Basisverzeichnis: {self.base_dir}")

    def add_sample(self, original_image_path: str, edited_image_path: str, txt_path: str):
        original_image_path = os.path.abspath(original_image_path)
        edited_image_path = os.path.abspath(edited_image_path)
        txt_path = os.path.abspath(txt_path)

        print(f"Originalbild Pfad: {original_image_path}")
        print(f"Bearbeitetes Bild Pfad: {edited_image_path}")
        print(f"Textdatei Pfad: {txt_path}")

        if not os.path.isfile(original_image_path):
            raise FileNotFoundError(f"Originalbild nicht gefunden: {original_image_path}")
        if not os.path.isfile(edited_image_path):
            raise FileNotFoundError(f"Bearbeitetes Bild nicht gefunden: {edited_image_path}")
        if not os.path.isfile(txt_path):
            raise FileNotFoundError(f"Textdatei nicht gefunden: {txt_path}")

        letter = self._extract_letter(original_image_path, edited_image_path, txt_path)
        folder_name = f"Dataset_{letter}"
        target_folder = os.path.join(self.base_dir, folder_name)
        os.makedirs(target_folder, exist_ok=True)

        shutil.copy(original_image_path, os.path.join(target_folder, 'original_' + os.path.basename(original_image_path)))
        shutil.copy(edited_image_path, os.path.join(target_folder, 'edited_' + os.path.basename(edited_image_path)))
        shutil.copy(txt_path, os.path.join(target_folder, os.path.basename(txt_path)))

    def get_sample(self, letter: str) -> DatasetSample:
        folder_name = f"Dataset_{letter}"
        target_folder = os.path.join(self.base_dir, folder_name)
        if not os.path.isdir(target_folder):
            raise ValueError(f"Kein Sample mit Buchstabe {letter} gefunden")
        return DatasetSample(target_folder)

    def _extract_letter(self, *paths) -> str:
        for path in paths:
            filename = os.path.basename(path)
            parts = filename.split('_')
            if len(parts) > 1 and len(parts[1]) > 0:
                return parts[1][0]  # z.B. "Test2_A.jpg" -> "A"
        raise ValueError("Kein gültiger Buchstabe im Dateinamen gefunden")

# Beispiel
if __name__ == '__main__':
    current_dir = os.path.dirname(os.path.abspath(__file__))
    dataset_dir = os.path.join(current_dir, 'Dataset')
    dataset = Dataset(dataset_dir)
    try:
        dataset.add_sample(os.path.join(current_dir, 'Dataset', 'Test2_A.jpg'),
                           os.path.join(current_dir, 'Dataset', 'bearbeitet_Test2_A.jpg'),
                           os.path.join(current_dir, 'Dataset', 'Test2_A.txt'))
        sample = dataset.get_sample('A')
        print(f"Originalbild: {sample.original_image}")
        print(f"Textdatei: {sample.textfile}")
        print(f"Bearbeitetes Bild: {sample.edited_image}")
    except FileNotFoundError as e:
        print(e)