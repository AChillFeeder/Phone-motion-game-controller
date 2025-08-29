# main.py — unified phone (UDP) + camera (MediaPipe)
import threading
import time

from dispatcher import SensorDispatcher
from sensor_receiver import SensorReceiver
from input_handler import InputHandler
from recognizers.phone_motion_recognizer import recognize as mqr_recognize

# Camera module we just wrapped
import recognizers.dash_detection as dash_detection

from config import CAMERA_ACTION_MAP  # e.g. {"dash_left":"dash_out", "dash_right":"dash_in", "jump":"jump"}

# ActionBus for volume keys
try:
    from action_bus import ActionBus
    HAVE_ACTIONBUS = True
except Exception:
    HAVE_ACTIONBUS = False

ih = InputHandler()
disp = SensorDispatcher()


def recognizer_callback(sensor_type: str, parts):
    try:
        x = y = z = 0.0
        if sensor_type in ("accel", "gyro") and len(parts) >= 4:
            x, y, z = float(parts[1]), float(parts[2]), float(parts[3])

        action_raw = mqr_recognize(sensor_type, x, y, z)
        if not action_raw:
            return

        normalized = action_raw.lower().replace(" ", "_")
        ih.handle(normalized)  # <-- make sure this is active

    except Exception as e:
        print(f"[main] recognizer_callback error: {e} | type={sensor_type} parts={parts}")


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
