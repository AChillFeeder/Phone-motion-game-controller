import asyncio
import pyautogui
import pydirectinput
import json
import time
import websockets
from recognize_movement import recognize_movement

# Optimize pyautogui settings
pyautogui.PAUSE = 0  # Disable automatic pauses for faster input
pyautogui.FAILSAFE = False  # Disable failsafe for more consistent behavior

# Constants for event types
EVENT_ATTACK = "Attack"
EVENT_PARRY = "Parry"
EVENT_DASH_IN = "Dash in"
EVENT_DASH_OUT = "Dash out"

# Preallocate frequently used objects and state
event_queue = asyncio.Queue()
combination_button = ""
current_time = time.monotonic
preallocated_data = {
    "gyro_x": 0,
    "gyro_y": 0,
    "gyro_z": 0,
    "accel_x": 0,
    "accel_y": 0,
    "accel_z": 0
}

# Preallocate sensor data structure
sensor_data = {"gyroscope": {}, "accelerometer": {}, "special_action": ""}

# WebSocket server handler
async def handle_sensor_data(websocket, path):
    global combination_button
    print("Connection established")
    
    try:
        async for message in websocket:
            data = json.loads(message)

            # Handle delay logging
            if data.get("delay"):
                print("delay:", data["delay"])

            # Process special actions
            special_action = data.get("special_action")
            if special_action:
                await process_special_action(special_action, websocket)

            # Process recognized movement
            action = recognize_movement(data)
            if action:
                # Use the event queue for asynchronous event handling
                await event_queue.put(action)

    except websockets.ConnectionClosed:
        print("Connection closed")


async def process_special_action(special_action, websocket):
    """Process special actions asynchronously."""
    global combination_button
    if special_action == "Camera lock":
        pyautogui.click(button='middle')
    elif special_action == "Deflect":
        print("deflect")
        pydirectinput.click(button='right')
        # Send response back to WebSocket client
        await websocket.send(json.dumps({"status": "Deflect executed"}))
    elif special_action == "Volume up":
        combination_button = "power" if combination_button != "power" else ""
        print("Combination button:", combination_button)
    else:
        print("Unrecognized action:", special_action)


async def process_event_queue():
    """Process the event queue asynchronously."""
    while True:
        event = await event_queue.get()
        await process_action(event, combination_button)
        event_queue.task_done()


async def process_action(action, combination_button):
    """Process movement-based actions asynchronously."""
    if action == EVENT_ATTACK:
        await perform_attack(combination_button)
    elif action == EVENT_PARRY:
        pydirectinput.click(button='right')
    elif action == EVENT_DASH_IN:
        await perform_dash('w')
    elif action == EVENT_DASH_OUT:
        await perform_dash('s')


async def perform_attack(combination_button):
    """Handle attack actions asynchronously."""
    if combination_button == "power":
        print("Combat art!")
        pydirectinput.mouseDown(button='right')
        pydirectinput.mouseDown(button='left')
        pydirectinput.mouseUp(button='left')
        pydirectinput.mouseUp(button='right')
    else:
        pydirectinput.click(button='left')


async def perform_dash(direction_key):
    """Handle dash actions asynchronously."""
    pydirectinput.keyDown(direction_key)
    pydirectinput.keyDown('shift')
    await asyncio.sleep(0.01)  # Minimal delay to simulate dash
    pydirectinput.keyUp(direction_key)
    pydirectinput.keyUp('shift')


async def start_server():
    """Start the WebSocket server with optimized ping."""
    server = await websockets.serve(handle_sensor_data, '0.0.0.0', 6790, ping_interval=None)
    print("Server started on ws://localhost:6790")
    
    # Start the event queue processor
    asyncio.create_task(process_event_queue())
    
    await server.wait_closed()


# Run the server
asyncio.run(start_server())
