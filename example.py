import requests

# API endpoint
url = "http://127.0.0.1:8000/process-image/"

# Path to the image file
image_path = "C:\\Users\\dhuma\\Downloads\\1627974061php0CN16E.jpeg"  # Replace with your image path

# Send the request
with open(image_path, "rb") as img_file:
    response = requests.post(url, files={"file": img_file})

# Print the output
print(response.json())
