from image_capture import capture_image
from image_recognition import recognize_objects
from path_calculation import calculate_path

def main():
    image_path = capture_image()
    graph_data = recognize_objects(image_path)
    path = calculate_path(graph_data)

    if path:
        print("valid")
    else:
        print("invalid")

if __name__ == "__main__":
    main()