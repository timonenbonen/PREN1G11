import cv2

def capture_image(filepath="captured.jpg"):
    print("[ImageCapture] Capturing image...")
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise Exception("Could not open camera.")
    ret, frame = cap.read()
    if ret:
        cv2.imwrite(filepath, frame)
    cap.release()
    print(f"[ImageCapture] Image saved to {filepath}")
    return filepath