import math
import time

# Thresholds
COOLDOWN_TIME = 0  # Minimum time between actions
GYRO_MAGNITUDE_THRESHOLD = 6
ACCEL_START_THRESHOLD = 3
ACCEL_STOP_THRESHOLD = 3
GYRO_PARRY_THRESHOLD = 4
GYRO_PARRY_THRESHOLD_STOP = 3
GYRO_DASH_THRESHOLD = 6
DASH_COOLDOWN_TIME = 1

# State variables
last_action_time = 0
last_dash_time = 0
can_attack = True
can_parry = True
last_parry_direction = 1

def recognize_movement(data):
    global last_action_time, last_dash_time, can_attack, can_parry
    current_time = time.time()

    if current_time - last_action_time < COOLDOWN_TIME:
        return None

    accel_x = data['accelerometer']['x']
    accel_y = data['accelerometer']['y']
    accel_z = data['accelerometer']['z']
    gyro_x = data['gyroscope']['x']
    gyro_y = data['gyroscope']['y']
    gyro_z = data['gyroscope']['z']

    accel_magnitude = math.sqrt(accel_x**2 + accel_y**2 + accel_z**2)
    gyro_magnitude = math.sqrt(gyro_x**2 + gyro_y**2 + gyro_z**2)

    # # Parry detection
    # if gyro_magnitude > GYRO_MAGNITUDE_THRESHOLD and gyro_y < GYRO_PARRY_THRESHOLD * -1 and can_parry:
    #     print("----- PARRY -----")
    #     print("gyro_y: ", gyro_y)
    #     can_parry = False
    #     last_action_time = current_time
    #     return "Parry"
    # if abs(gyro_y) < GYRO_PARRY_THRESHOLD_STOP:
    #     can_parry = True

    # Attack detection
    if accel_magnitude > ACCEL_START_THRESHOLD and can_attack: #and gyro_magnitude < GYRO_MAGNITUDE_THRESHOLD:
        can_attack = False
        print("------------ Attack ------------")
        print("gyro y: ", gyro_y)
        last_action_time = current_time
        return "Attack"
    if accel_magnitude < ACCEL_STOP_THRESHOLD:
        can_attack = True

    if not can_attack: # avoid breaking the attack by another action, attacks are commits now
        return None

    # Dash detection
    if abs(gyro_x) > GYRO_DASH_THRESHOLD and current_time - last_dash_time > DASH_COOLDOWN_TIME:
        last_action_time = current_time
        last_dash_time = current_time
        direction = "in" if gyro_x < 0 else "out"
        print(f"----- Dash {direction} -----")
        print(abs(gyro_x))
        return "Dash " + direction

    return None
