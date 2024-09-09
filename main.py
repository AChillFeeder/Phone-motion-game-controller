import asyncio
import websockets
import pyautogui
from recognize_movement import recognize_movement
import json
import pydirectinput


# WebSocket server handler
async def handle_sensor_data(websocket, path):
    print("Connection established")
    try:
        while True:
            message = await websocket.recv()  # Manually receive the data
            data = json.loads(message)

            # print(f"Received sensor data: {data}")  # Print the received message
             # Call the movement recognition function
            action = recognize_movement(data)
            
            if action:
                print(f"Recognized movement: {action}")
    
            if action == "Attack":
                pyautogui.mouseDown(button='left')
                pyautogui.mouseUp(button='left')
                # pass

            if action == "Parry":
                # pass
                pyautogui.mouseDown(button='right')
                pyautogui.mouseUp(button='right')

            if action == "Dash":
                # pass
                pydirectinput.keyDown('shift')
                pydirectinput.keyUp('shift')

    
    except websockets.ConnectionClosed:
        print("Connection closed")


# Start the WebSocket server
async def start_server():
    server = await websockets.serve(handle_sensor_data, '0.0.0.0', 6790)
    print("Server started on ws://0.0.0.0:6790")
    await server.wait_closed()

# Run the server
asyncio.run(start_server())
