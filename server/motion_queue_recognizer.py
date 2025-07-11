from collections import deque
import time
import math

# === CONFIGURATION ===
MAX_QUEUE_LENGTH = 30
ACCEL_ATTACK_THRESHOLD = 25.0      # Trigger motion if recent speed exceeds this
ACCEL_END_SPEED_THRESHOLD = 5.0   # End motion when speed falls below this
GYRO_PARRY_THRESHOLD = 4.0         # Optional: for rotation-based detection

# === STATE ===
accel_queue = deque(maxlen=MAX_QUEUE_LENGTH)
gyro_queue = deque(maxlen=MAX_QUEUE_LENGTH)

motion_active = False
motion_phase = None  # "attack", "parry", or None


# === HELPERS ===
def add_to_queue(sensor_type, x, y, z):
    entry = {'x': x, 'y': y, 'z': z, 't': time.time()}
    if sensor_type == "accel":
        accel_queue.append(entry)
    elif sensor_type == "gyro":
        gyro_queue.append(entry)

def recent_speed():
    if len(accel_queue) < 2:
        return 0.0
    a = accel_queue[-2]
    b = accel_queue[-1]
    dx = b['x'] - a['x']
    dy = b['y'] - a['y']
    dz = b['z'] - a['z']
    return math.sqrt(dx**2 + dy**2 + dz**2)


# === MOTION DETECTION ===
def detect_attack_start():
    return recent_speed() > ACCEL_ATTACK_THRESHOLD

def detect_attack_end():
    return recent_speed() < ACCEL_END_SPEED_THRESHOLD

# === Optional: For rotation-based actions
def detect_parry_start():
    return any(abs(d['y']) > GYRO_PARRY_THRESHOLD for d in reversed(gyro_queue))

def detect_parry_end():
    return all(abs(d['y']) < GYRO_PARRY_THRESHOLD * 0.4 for d in gyro_queue)


# === MAIN ENTRYPOINT ===
def recognize(sensor_type, x, y, z):
    global motion_active, motion_phase

    # Special case: Volume Up (simulate parry)
    if sensor_type == "key" and x == "volup":
        print("[PARRY] Volume Up triggered")
        return "Parry"

    add_to_queue(sensor_type, x, y, z)

    if not motion_active:
        if sensor_type == "accel" and detect_attack_start():
            motion_active = True
            motion_phase = "attack"
            speed = recent_speed()
            print(f"[ATTACK START] Speed: {speed:.2f}")
            return "Attack"

    elif motion_active:
        if motion_phase == "attack" and sensor_type == "accel" and detect_attack_end():
            motion_active = False
            motion_phase = None

    return None
