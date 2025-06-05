# camera_client.py

import requests

def capture_picture_from_api(
    api_url="http://localhost:8000/take_picture",
    save_path="/tmp/picture.jpg"
) -> str:
    """Fetches an image from the FastAPI endpoint and saves it locally."""
    response = requests.get(api_url)
    if response.status_code != 200:
        raise RuntimeError(f"❌ Failed to get image from API: {response.status_code}")

    with open(save_path, "wb") as f:
        f.write(response.content)

    return save_path