import socket
import time
from motion_queue_recognizer import recognize
from input_handler import InputHandler
from math import isclose
from mathutils import Quaternion, Vector

input_handler = InputHandler()

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", 9001))

print("Listening for packets...\n")

last_upright_state = None

def check_upright_orientation(q: Quaternion) -> bool:
    """Returns True if phone is upright (bottom down, screen vertical)."""
    local_up = Vector((0, -1, 0))  # 'Up' in phone space
    world_up = q @ local_up       # Transform to world space
    dot = world_up.dot(Vector((0, 0, -1)))  # Gravity is 'down'

    return dot > 0.9  # Very close to upright (tweak threshold if needed)

def test_delay(timestamp_ms: int, lag_test_flag: str):
    now_ms = int(time.time() * 1000)
    delay_ms = now_ms - timestamp_ms

    if lag_test_flag.lower() == "true":
        print(f"[LAG TEST ON] Round-trip delay: {delay_ms} ms at {time.strftime('%H:%M:%S')}")
    return delay_ms

while True:
    data, _ = sock.recvfrom(1024)
    try:
        decoded = data.decode().strip()
        parts = decoded.split(",")

        sensor_type = parts[0].lower()

        if sensor_type == "rotq" and len(parts) == 7:
            x, y, z, w = map(float, parts[1:5])
            timestamp = int(parts[5])
            lag_flag = parts[6]

            quat = Quaternion((w, x, y, z))

            is_upright = check_upright_orientation(quat)

            if last_upright_state is None or is_upright != last_upright_state:
                last_upright_state = is_upright
                if is_upright:
                    print("[ORIENTATION] Phone is upright (bottom facing floor)")
                else:
                    print("[ORIENTATION] Phone is tilted / not upright")

        elif sensor_type in ("accel", "gyro") and len(parts) == 6:
            x, y, z = map(float, parts[1:4])
            timestamp = int(parts[4])

            action = recognize(sensor_type, x, y, z)
            if action:
                print(f"[ACTION] {action}")
                input_handler.handle(action)

        # elif sensor_type == "rotq" and len(parts) == 7:
        #     x, y, z, w = map(float, parts[1:5])
        #     timestamp = int(parts[5])
            # print(f"[ROTQ] Quaternion received: ({w:.3f}, {x:.3f}, {y:.3f}, {z:.3f})")

        elif sensor_type == "volkey" and len(parts) == 3:
            # input type, keyCode, timestamp
            # 25 down, 24 up
            key_mapping = {
                "25": "down",
                "24": "up"
            }
            key_type = key_mapping[parts[1]]

            timestamp = int(parts[2])

            print(f"[KEY EVENT] Volume button: {key_type.upper()} at {time.strftime('%H:%M:%S')}")
            # ! Refactor this shit
            if key_type == "down":
                action = "parry"
                input_handler.handle(action)
            if key_type == "up":
                action = "jump"
                input_handler.handle(action)

        else:
            print(f"[ERROR] Malformed packet: {decoded}")

    except Exception as e:
        print(f"[EXCEPTION] {e} | Raw: {data}")
