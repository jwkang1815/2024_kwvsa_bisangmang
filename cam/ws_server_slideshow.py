import asyncio
import websockets
import cv2
import base64
import numpy as np
import os
import time

async def video_stream(websocket, image_files, image_dir):
    print(f"Client connected: {websocket.remote_address}")

    try:
        for image_file in image_files:
            image_path = os.path.join(image_dir, image_file)
            # Check if file is a valid image
            if not os.path.isfile(image_path) or not image_file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
              print(f"Skipping invalid file: {image_file}")
              continue
            frame = cv2.imread(image_path)

            if frame is None:
                error_message = f"Error: Could not read image {image_file}."
                print(error_message)
                await websocket.send(error_message)
                continue

            # Resize the image
            frame = cv2.resize(frame, (640, 480))

            # Encode the frame as JPEG
            _, buffer = cv2.imencode('.jpg', frame)
            # Encode JPEG buffer to base64
            frame_base64 = base64.b64encode(buffer).decode('utf-8')

            await websocket.send(frame_base64)
            await asyncio.sleep(1) # Adjust sleep time for slideshow speed

        # Send a completion message after all images are sent
        await websocket.send("Slideshow completed.")

    except websockets.exceptions.ConnectionClosed:
        print(f"Client disconnected: {websocket.remote_address}")
    except Exception as e:
        print(f"An error occurred: {e}")
        await websocket.send(f"Server Error: {e}")

async def main():
    image_dir = "C:/Test_images"  # Replace with your image directory
    image_files = sorted(os.listdir(image_dir)) # Sort to maintain order

    async def handler(websocket):
        await video_stream(websocket, image_files, image_dir)

    async with websockets.serve(handler, "0.0.0.0", 8765):
        print("WebSocket server started on ws://0.0.0.0:8765")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())