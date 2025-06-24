from collections import deque
import time
import math

# Constants
MAX_QUEUE_LENGTH = 30
GYRO_PARRY_THRESHOLD = 15.0
ACCEL_ATTACK_THRESHOLD = 45.0
GRAVITY_Z = 9.81

# State
gyro_queue = deque(maxlen=MAX_QUEUE_LENGTH)
accel_queue = deque(maxlen=MAX_QUEUE_LENGTH)
motion_active = False

def add_to_queue(sensor_type, x, y, z):
    entry = {'x': x, 'y': y, 'z': z, 't': time.time()}
    if sensor_type == "gyro":
        gyro_queue.append(entry)
    elif sensor_type == "accel":
        accel_queue.append(entry)

def detect_attack_ready():
    if len(accel_queue) < 2:
        return False
    dx = accel_queue[-1]['x'] - accel_queue[0]['x']
    dy = accel_queue[-1]['y'] - accel_queue[0]['y']
    dz = (accel_queue[-1]['z'] - GRAVITY_Z) - (accel_queue[0]['z'] - GRAVITY_Z)
    delta_mag = math.sqrt(dx**2 + dy**2 + dz**2)
    return delta_mag > ACCEL_ATTACK_THRESHOLD

def detect_attack_done():
    if len(accel_queue) < 2:
        return True
    dx = accel_queue[-1]['x'] - accel_queue[0]['x']
    dy = accel_queue[-1]['y'] - accel_queue[0]['y']
    dz = (accel_queue[-1]['z'] - GRAVITY_Z) - (accel_queue[0]['z'] - GRAVITY_Z)
    delta_mag = math.sqrt(dx**2 + dy**2 + dz**2)
    return delta_mag < ACCEL_ATTACK_THRESHOLD * 0.5

def detect_parry_ready():
    return any(abs(d['y']) > GYRO_PARRY_THRESHOLD for d in reversed(gyro_queue))

def detect_parry_done():
    return all(abs(d['y']) < GYRO_PARRY_THRESHOLD * 0.5 for d in gyro_queue)

def recognize(sensor_type, x, y, z):
    global motion_active

    add_to_queue(sensor_type, x, y, z)

    if not motion_active:
        if detect_attack_ready():
            motion_active = True
            return "Attack"
        elif detect_parry_ready():
            motion_active = True
            return "Parry"

    else:
        # Reset when motion ends (no need to return anything)
        if detect_attack_done() and detect_parry_done():
            motion_active = False

    return None
