import time

# Thresholds
COOLDOWN_TIME = 0  # Minimum time between actions
GYRO_MAGNITUDE_THRESHOLD_SQ = 6 ** 2  # Squared values to avoid costly sqrt operations
ACCEL_START_THRESHOLD_SQ = 3 ** 2
ACCEL_STOP_THRESHOLD_SQ = 3 ** 2
GYRO_PARRY_THRESHOLD = 4
GYRO_PARRY_THRESHOLD_STOP = 3
GYRO_DASH_THRESHOLD = 6
DASH_COOLDOWN_TIME = 1

# State variables
last_action_time = 0
last_dash_time = 0
can_attack = True
can_parry = True


def recognize_movement(data):
    global last_action_time, last_dash_time, can_attack, can_parry

    # Get the current time once, avoid repeated calls
    current_time = time.time()

    # Exit early if within cooldown period
    if current_time - last_action_time < COOLDOWN_TIME:
        return None

    # Extract data once, avoid multiple accesses to the same data
    accel_x = data['accelerometer']['x']
    accel_y = data['accelerometer']['y']
    accel_z = data['accelerometer']['z']
    gyro_x = data['gyroscope']['x']
    gyro_y = data['gyroscope']['y']

    # Use squared magnitudes to avoid costly sqrt operations
    accel_magnitude_sq = accel_x ** 2 + accel_y ** 2 + accel_z ** 2
    gyro_magnitude_sq = gyro_x ** 2 + gyro_y ** 2  # No need to include gyro_z in this case

    # Attack detection (committed attack logic)
    if can_attack and accel_magnitude_sq > ACCEL_START_THRESHOLD_SQ:
        can_attack = False  # Commit to the attack
        last_action_time = current_time
        # print("------------ Attack ------------")
        # print("gyro y: ", gyro_y)
        return "Attack"

    if accel_magnitude_sq < ACCEL_STOP_THRESHOLD_SQ:
        can_attack = True  # Reset attack eligibility when acceleration drops below threshold

    # Early return to avoid breaking the attack by another action
    if not can_attack:
        return None

    # Dash detection (use squared values for comparison)
    if abs(gyro_x) > GYRO_DASH_THRESHOLD and current_time - last_dash_time > DASH_COOLDOWN_TIME:
        last_action_time = current_time
        last_dash_time = current_time
        direction = "in" if gyro_x < 0 else "out"
        # print(f"----- Dash {direction} -----")
        return "Dash " + direction

    return None
