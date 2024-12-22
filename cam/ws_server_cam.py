import asyncio
import websockets
import cv2
import base64
import numpy as np

capture = cv2.VideoCapture(0)
capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

async def video_stream(websocket):
    print(f"Client connected: {websocket.remote_address}")
    # Webcam Verification
    
    if not capture.isOpened():
        error_message = "Error: Could not open webcam."
        print(error_message)
        await websocket.send(error_message)  # Send error to client
        return

    try:
        while True:
            ret, frame = capture.read()
            if not ret:
                error_message = "Error: Could not read frame from webcam."
                print(error_message)
                await websocket.send(error_message) # Send error to client
                break

            # Encode the frame as JPEG
            _, buffer = cv2.imencode('.jpg', frame)
            # Encode JPEG buffer to base64
            frame_base64 = base64.b64encode(buffer).decode('utf-8')

            await websocket.send(frame_base64)
            await asyncio.sleep(0.5)

    except websockets.exceptions.ConnectionClosed:
        print(f"Client disconnected: {websocket.remote_address}")
    except Exception as e:
        print(f"An error occurred: {e}")
        await websocket.send(f"Server Error: {e}")
    finally:
        capture.release()
        print("Webcam released.")

async def main():
    async with websockets.serve(video_stream, "0.0.0.0", 8765):
        print("WebSocket server started on ws://0.0.0.0:8765")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())