import asyncio
import websockets
import pyautogui
from recognize_movement import recognize_movement
from pynput.mouse import Button, Controller as MouseController
import json
from pynput.keyboard import Controller

keyboard = Controller()
mouse = MouseController()

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
                # mouse.click(Button.left, 1)
                pyautogui.mouseDown(button='left')
                pyautogui.mouseUp(button='left')

            if action == "Parry":
                # mouse.click(Button.right, 1)
                pyautogui.mouseDown(button='right')
                pyautogui.mouseUp(button='right')

            if action == "Dash":
                pass
                pyautogui.keyDown('shift')
                pyautogui.press('s')
                pyautogui.keyUp('shift')

    
    except websockets.ConnectionClosed:
        print("Connection closed")


# Start the WebSocket server
async def start_server():
    server = await websockets.serve(handle_sensor_data, '0.0.0.0', 6790)
    print("Server started on ws://0.0.0.0:6790")
    await server.wait_closed()

# Run the server
asyncio.run(start_server())
