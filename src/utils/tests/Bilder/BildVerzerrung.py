import cv2
import numpy as np


def select_points(image_path):
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError("Bild konnte nicht geladen werden")

    points = []

    def click_event(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            points.append((x, y))
            cv2.circle(image, (x, y), 5, (0, 0, 255), -1)
            cv2.imshow("Bild", image)
        if len(points) == 4:
            cv2.destroyAllWindows()

    cv2.imshow("Bild", image)
    cv2.setMouseCallback("Bild", click_event)
    cv2.waitKey(0)
    return points


def warp_image(image_path, dst_points, output_path):
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError("Bild konnte nicht geladen werden")

    height, width = image.shape[:2]
    src_points = [(0, 0), (width, 0), (width, height), (0, height)]

    matrix = cv2.getPerspectiveTransform(np.float32(src_points), np.float32(dst_points))
    warped = cv2.warpPerspective(image, matrix, (width, height))

    cv2.imwrite(output_path, warped)
    print(f"Verzerrtes Bild gespeichert unter: {output_path}")


if __name__ == "__main__":
    input_image = r"C:\Users\marin\PycharmProjects\PREN1G11\src\utils\tests\Bilder\MusterBoden\IMG20250324095259.jpg"
    output_image = "output.jpg"

    print("Bitte wähle 4 Punkte im Bild aus.")
    dst_pts = select_points(input_image)

    warp_image(input_image, dst_pts, output_image)
