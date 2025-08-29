from collections import deque
import time
import math

# === CONFIG ===
MAX_QUEUE_LENGTH = 40

# Attack from accelerometer: use sample-to-sample delta magnitude (same behavior as before)
ACCEL_ATTACK_DELTA = 25.0       # Trigger when last accel delta magnitude exceeds this
ACCEL_END_DELTA    = 5.0        # End attack when accel delta falls below this
ATTACK_REFRACTORY_MS = 150      # Minimum time between attack start events

# Parry from gyro (rotation around Y)
GYRO_PARRY_THRESHOLD = 4.0      # Start parry if any recent |gyro.y| exceeds this
PARRY_END_THRESHOLD  = GYRO_PARRY_THRESHOLD * 0.4
PARRY_REFRACTORY_MS  = 150

# === STATE ===
accel_queue = deque(maxlen=MAX_QUEUE_LENGTH)
gyro_queue  = deque(maxlen=MAX_QUEUE_LENGTH)

state = "idle"                  # "idle" | "attack" | "parry"
last_fired_ms = 0               # time of last start event (attack/parry)


# === HELPERS ===
def _now_ms() -> int:
    return int(time.time() * 1000)

def _push(q: deque, x: float, y: float, z: float):
    q.append({'x': x, 'y': y, 'z': z, 't': _now_ms()})

def _delta_mag(q: deque) -> float:
    """Magnitude of delta between the last two samples (unitless; same as original)."""
    if len(q) < 2:
        return 0.0
    a, b = q[-2], q[-1]
    dx = b['x'] - a['x']
    dy = b['y'] - a['y']
    dz = b['z'] - a['z']
    return math.sqrt(dx*dx + dy*dy + dz*dz)

def _gyro_y_peak(q: deque) -> float:
    """Maximum absolute Y rotation observed in the queue."""
    if not q:
        return 0.0
    return max(abs(s['y']) for s in q)


# === MAIN ENTRYPOINT ===
def recognize(sensor_type: str, x: float, y: float, z: float):
    """
    Called on every incoming phone sample.
    Returns one of: "Attack", "Parry", or None (only on START events).
    """
    global state, last_fired_ms

    # Route sample to the right queue
    if sensor_type == "accel":
        _push(accel_queue, x, y, z)
    elif sensor_type == "gyro":
        _push(gyro_queue, x, y, z)
    else:
        # Ignore unknown types; volkeys are handled via ActionBus in main.py
        return None

    now = _now_ms()

    # --- State machine ---
    if state == "idle":
        if sensor_type == "accel":
            speed = _delta_mag(accel_queue)
            if speed > ACCEL_ATTACK_DELTA and (now - last_fired_ms) >= ATTACK_REFRACTORY_MS:
                state = "attack"
                last_fired_ms = now
                print(f"[ATTACK START] Speed: {speed:.2f}")
                return "Attack"

        elif sensor_type == "gyro":
            peak = _gyro_y_peak(gyro_queue)
            if peak > GYRO_PARRY_THRESHOLD and (now - last_fired_ms) >= PARRY_REFRACTORY_MS:
                state = "parry"
                last_fired_ms = now
                print(f"[PARRY START] GyroY peak: {peak:.2f}")
                return "Parry"

    elif state == "attack":
        if sensor_type == "accel":
            speed = _delta_mag(accel_queue)
            if speed < ACCEL_END_DELTA:
                state = "idle"  # no end event returned; only starts generate actions

    elif state == "parry":
        if sensor_type == "gyro":
            peak = _gyro_y_peak(gyro_queue)
            if peak < PARRY_END_THRESHOLD:
                state = "idle"

    return None
