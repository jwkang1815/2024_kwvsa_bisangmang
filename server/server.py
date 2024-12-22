from flask import Flask, render_template, Response, send_from_directory, request
from time import sleep
import cv2
import json
import random
import time
import shutil
import websockets
import asyncio
import base64
import numpy as np
import pandas as pd
import threading
import os
import keras
import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import img_to_array
from tensorflow.keras.preprocessing.image import load_img
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from flask import Flask, render_template, request


app = Flask(__name__,
            static_url_path='', 
            static_folder='static',
            template_folder='templates')

# Global variable to store the latest image filename
latest_image_filename = None
image_filename_lock = threading.Lock()  # Create a lock for the image filename

model = tf.keras.models.load_model('./model/effNet.keras')
class_names = ["Bird", "Drone", "None"]
old_dir = './static/images/logs'

# Directory to save captured images
CAPTURE_DIR = "./static/images/incomming"
if not os.path.exists(CAPTURE_DIR):
    os.makedirs(CAPTURE_DIR)


async def connect_to_websocket():
    uri = "ws://<CAAM_ADDR>:8765"  # Replace with your cam web socket IP
    async with websockets.connect(uri) as websocket:
        print(f"Connected to WebSocket server at {uri}")
        while True:
            try:
                message = await websocket.recv()
                # Decode the base64 encoded JPEG frame
                frame_bytes = base64.b64decode(message)
                # Convert bytes to numpy array
                npimg = np.frombuffer(frame_bytes, dtype=np.uint8)
                # Decode numpy array to frame
                frame = cv2.imdecode(npimg, cv2.IMREAD_COLOR)

                # Save the frame as JPEG
                save_frame_as_jpeg(frame)

            except websockets.exceptions.ConnectionClosed:
                print("WebSocket connection closed.")
                break
            except Exception as e:
                print(f"Error: {e}")
                break


def save_frame_as_jpeg(frame):
    """Saves the given frame as a JPEG file in the CAPTURE_DIR."""
    global latest_image_filename
    timestamp = time.time()  # Use Unix timestamp for unique filenames
    filename = os.path.join(CAPTURE_DIR, f"frame_{timestamp}.jpg")
    cv2.imwrite(filename, frame)
    print(f"Saved frame to {filename}")

    with image_filename_lock:
        latest_image_filename = filename


def prediction(img_name):
    img = load_img(img_name, target_size=(256, 256, 3))
    img = img_to_array(img)
    img = img / 255.0

    pred = model.predict(np.expand_dims(img, axis=0))
    pred_class = np.argmax(pred, axis=1)[0]
    acc_dividend = pred[0][0] + pred[0][1] + pred[0][2]

    # 0: Bird, 1: Drone, 2: None 
    accuracy_0 = pred[0][0]/acc_dividend*100
    accuracy_1 = pred[0][1]/acc_dividend*100
    accuracy_2 = pred[0][2]/acc_dividend*100

    return (class_names[pred_class], f"{accuracy_0:.3f}"+'%', f"{accuracy_1:.3f}"+'%', f"{accuracy_2:.3f}"+'%')


def generate_frames():
    global latest_image_filename
    while True:
        # Get the latest image filename (thread-safe)
        with image_filename_lock:
            current_image_filename = latest_image_filename
        
        if current_image_filename:
            pred_class, acc_bird, acc_drone, acc_none = prediction(current_image_filename)

            # Generate annotations (replace with your logic)
            annotations = {
                "Prediction": pred_class,
                "Bird": acc_bird,
                "Drone": acc_drone,
                "None": acc_none
            }
            # Encode annotations as JSON
            annotations_json = json.dumps(annotations)

            # Yield the image filename and annotations in a custom format
            yield (f'--frame\r\n'
                   f'Content-Type: text/plain\r\n\r\n{current_image_filename}\r\n'
                   f'--frame\r\n'
                   f'Content-Type: application/json\r\n\r\n{annotations_json}\r\n')
        
        # sleep(0.05)  # Adjust sleep time as needed


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/stream')
def stream():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/images/incomming/<path:filename>')
def serve_image(filename):
    """Serve static images from the CAPTURE_DIR."""
    return send_from_directory(CAPTURE_DIR, filename)

if __name__ == "__main__":
    # Start the WebSocket client in a separate thread
    threading.Thread(target=lambda: asyncio.run(connect_to_websocket()), daemon=True).start()
    app.run(host="<HOST_IP>", port="8080", debug=True) # Replace with your server's IP