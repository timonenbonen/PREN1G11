from fastapi import FastAPI
from image_capture import capture_image
from image_recognition import recognize_objects
from path_calculation import calculate_path
from fastapi.responses import FileResponse

app = FastAPI()

@app.post("/calculate")
def calculate_route():
    try:
        image_path = capture_image()
        graph_data = recognize_objects(image_path)
        path = calculate_path(graph_data)

        if path:
            return { "status": "valid", "path": path }
        else:
            return { "status": "invalid", "path": [] }

    except Exception as e:
        return { "status": "error", "message": str(e) }

@app.get("/take_picture")
def take_picture():
    image_path = capture_image()  # returns something like "captured.jpg"
    return FileResponse(image_path, media_type="image/jpeg", filename="captured.jpg")