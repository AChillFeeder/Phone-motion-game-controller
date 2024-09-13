import asyncio
import websockets
import pyautogui
from recognize_movement import recognize_movement
import json
import pydirectinput
import time

# pyautogui.PAUSE = 0

# WebSocket server handler
async def handle_sensor_data(websocket, path):
    print("Connection established")
    combination_button = ""
    try:
        while True:
            message = await websocket.recv()  # Manually receive the data
            data = json.loads(message)

            special_action = data["special_action"]
            if special_action:
                print(f"Special action: {special_action}")
                match special_action:
                    case "Camera lock":
                        pyautogui.mouseDown(button='middle')
                        pyautogui.mouseUp(button='middle')
                    case "Deflect":
                        pydirectinput.mouseDown(button='right')
                        pydirectinput.mouseUp(button='right')

                        response = {"status": "Deflect executed"}
                        await websocket.send(json.dumps(response))  # Send JSON response back to client
                    case "Volume up":
                        combination_button = "power" if combination_button != "power" else ""
                    case _:
                        print("unrecognized action")
                
            action = recognize_movement(data)
            if action:
                print(f"Recognized movement: {action}")
                if action == "Attack":
                    if combination_button == "power":
                        print("Combat art!")
                        pyautogui.mouseDown(button='right')
                        pyautogui.mouseDown(button='left')
                        pyautogui.mouseUp(button='left')
                        pyautogui.mouseUp(button='right')
                        combination_button = ""
                    else:
                        pydirectinput.mouseDown(button='left')
                        pydirectinput.mouseUp(button='left')
                elif action == "Parry":
                    pydirectinput.mouseDown(button='right')
                    pydirectinput.mouseUp(button='right')
                elif action == "Dash in":
                    pydirectinput.keyDown('w')
                    pydirectinput.keyDown('shift')
                    pydirectinput.keyUp('w')
                    pydirectinput.keyUp('shift')
                elif action == "Dash out":
                    pydirectinput.keyDown('s')
                    pydirectinput.keyDown('shift')
                    pydirectinput.keyUp('s')
                    pydirectinput.keyUp('shift')

    except websockets.ConnectionClosed:
        print("Connection closed")

# Start the WebSocket server
async def start_server():
    server = await websockets.serve(handle_sensor_data, '192.168.1.181', 6790)
    print("Server started on ws://192.168.1.181:6790")
    await server.wait_closed()

# Run the server
asyncio.run(start_server())
