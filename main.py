import asyncio
import websockets
import pyautogui
from recognize_movement import recognize_movement
import json
import pydirectinput


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
                print(f"Special action: {special_action}")  # Print the received message
                
                match special_action:
                    case "Camera lock":
                        pyautogui.mouseDown(button='middle')
                        pyautogui.mouseUp(button='middle')
                    case "Heal":
                        pydirectinput.keyDown('r')
                        pydirectinput.keyUp('r')
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
                        # combat art
                        pyautogui.mouseDown(button='right')
                        pyautogui.mouseDown(button='left')
                        pyautogui.mouseUp(button='left')
                        pyautogui.mouseUp(button='right')
                        combination_button = ""
                    else:
                        pyautogui.mouseDown(button='left')
                        pyautogui.mouseUp(button='left')

                if action == "Parry":
                    pyautogui.mouseDown(button='right')
                    pyautogui.mouseUp(button='right')

                if action == "Dash in":
                    # pass
                    pydirectinput.keyDown('w')
                    pydirectinput.keyDown('shift')
                    pydirectinput.keyUp('w')
                    pydirectinput.keyUp('shift')

                if action == "Dash out":
                    # pydirectinput.press('s')
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
