# main.py — unified phone (UDP) + camera (MediaPipe)
import threading
import time

from dispatcher import SensorDispatcher
from sensor_receiver import SensorReceiver
from input_handler import InputHandler
from motion_queue_recognizer import recognize as mqr_recognize

# Optional dict-based recognizer
try:
    from recognize_movement import recognize_movement as rm_recognize
    USE_RM = True
except Exception:
    USE_RM = False

# Camera module we just wrapped
import camera_recognizer.dash_detection as dash_detection

# Optional config mapping (if you have it)
try:
    from config import CAMERA_ACTION_MAP  # e.g. {"dash_left":"dash_out", "dash_right":"dash_in", "jump":"jump"}
except Exception:
    CAMERA_ACTION_MAP = {
        # By default only "jump" maps to an action you already have.
        # Fill these if you want left/right dashes to do something:
        # "dash_left":  "dash_out",   # example
        # "dash_right": "dash_in",    # example
        "jump": "jump",
    }

# ActionBus for volume keys
try:
    from action_bus import ActionBus
    HAVE_ACTIONBUS = True
except Exception:
    HAVE_ACTIONBUS = False

ih = InputHandler()
disp = SensorDispatcher()

# Keep last known sensor values for rm_recognize(data_dict)
last_sample = {
    "accelerometer": {"x": 0.0, "y": 0.0, "z": 0.0},
    "gyroscope": {"x": 0.0, "y": 0.0, "z": 0.0},
}

def recognizer_callback(sensor_type: str, parts):
    """
    Receives (sensor_type, parts_list) from SensorReceiver.
    Feeds phone recognizers and triggers InputHandler on first match.
    """
    try:
        x = y = z = 0.0
        if len(parts) >= 4:
            x, y, z = float(parts[1]), float(parts[2]), float(parts[3])

        # Update dict for rm_recognize
        if sensor_type == "accel":
            last_sample["accelerometer"] = {"x": x, "y": y, "z": z}
        elif sensor_type == "gyro":
            last_sample["gyroscope"] = {"x": x, "y": y, "z": z}

        # (1) queue-based recognizer
        act1 = mqr_recognize(sensor_type, x, y, z)
        # (2) dict-based recognizer
        act2 = rm_recognize(last_sample) if USE_RM else None

        action_raw = act1 or act2
        if not action_raw:
            return

        # Normalize action names (java_server uses "Attack", "Parry", "Dash in/out", ...)
        normalized = action_raw.lower().replace(" ", "_")
        # ih.handle(normalized)

    except Exception as e:
        print(f"[main] recognizer_callback error: {e} | parts={parts}")

# Register phone recognizer callback
disp.register(recognizer_callback)

def start_phone_receiver():
    receiver = SensorReceiver(dispatcher=disp, host="0.0.0.0", port=9001)
    receiver.listen()  # blocking → run in a thread

def start_camera():
    # Map camera events to InputHandler (or just print if unmapped)
    def on_cam_event(name: str):
        mapped = CAMERA_ACTION_MAP.get(name)
        if mapped:
            print(f"[CAMERA] {name} → {mapped}")
            ih.handle(mapped)
        else:
            print(f"[CAMERA] {name} (no action mapped)")

    dash_detection.run(on_event=on_cam_event, show_window=True)

def _wire_actionbus():
    if not HAVE_ACTIONBUS:
        return
    # Your phone sends numeric volkey codes; map them here
    def _on_vk(code: str, ts_ms: int):
        if str(code) == "25":   # volume down
            ih.handle("parry")
        elif str(code) == "24": # volume up
            ih.handle("jump")
        else:
            print(f"[main] Unknown volume key code: {code}")
    ActionBus.on_volume_key(_on_vk)

def main():
    print("[main] Booting Motion Controller (phone + camera)")
    _wire_actionbus()

    # Start phone UDP receiver
    t_phone = threading.Thread(target=start_phone_receiver, daemon=True)
    t_phone.start()

    # Start camera recognition
    t_cam = threading.Thread(target=start_camera, daemon=True)
    t_cam.start()

    # Keep alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[main] Shutting down...")

if __name__ == "__main__":
    main()
