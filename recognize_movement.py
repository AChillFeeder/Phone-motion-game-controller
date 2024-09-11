import math
import time

# Thresholds

## Global
COOLDOWN_TIME = 0.25  # Minimum time between actions
GYRO_MAGNITUDE_THRESHOLD = 8

## SLASH / ATTACK
ACCEL_START_THRESHOLD = 3  # Minimum acceleration to start tracking motion
ACCEL_STOP_THRESHOLD = 2   # Acceleration threshold to stop tracking
# DISTANCE_SLASH_THRESHOLD = 40  # Minimum total distance to consider it a slash
# NUMBER_OF_RECORDS_IN_MOTION_THRESHOLD = 6

## PARRY
GYRO_PARRY_THRESHOLD = 7  # Angular velocity threshold for detecting a parry (wrist twist)

## DASH
GYRO_DASH_THRESHOLD = 8
DASH_COOLDOWN_TIME = 1

# State variables
last_action_time = 0  # track action cooldown
last_dash_time = 0 # track dash cooldown
can_attack = True # one big slash would count for many attacks, so we wait until motion ends to allow next attack
initial_time = 0 
# tracking_motion = 0

# action_total_velocity = 0
# number_of_records_in_motion = 0

def recognize_movement(data):
    global last_action_time, last_dash_time, can_attack, tracking_motion, initial_time, action_total_velocity, number_of_records_in_motion
    current_time = time.time()

    # If we are still within the cooldown period, don't process any movements
    if current_time - last_action_time < COOLDOWN_TIME:
        return None

    # Extract accelerometer and gyroscope data
    accel_x = data['accelerometer']['x']
    accel_y = data['accelerometer']['y']
    accel_z = data['accelerometer']['z']
    
    gyro_x = data['gyroscope']['x']
    gyro_y = data['gyroscope']['y']
    gyro_z = data['gyroscope']['z']  # Z-axis for wrist twisting

    # Calculate the magnitude of acceleration and gyroscope rotation (angular velocity)
    accel_magnitude = math.sqrt(accel_x**2 + accel_y**2 + accel_z**2)
    gyro_magnitude = math.sqrt(gyro_x**2 + gyro_y**2 + gyro_z**2)


    # Attack doesn't take priority
    if accel_magnitude > ACCEL_START_THRESHOLD and can_attack:
        can_attack = False
        print("------------ Attack ------------")
        print(f"Acceleration magnitude: {accel_magnitude}")
        print("------------ End motion ------------")
        action_total_velocity = 0
        number_of_records_in_motion = 0
        return "Attack"
    if accel_magnitude < ACCEL_STOP_THRESHOLD:
        can_attack = True

    # Parry and Dash take priority
    if gyro_magnitude > GYRO_MAGNITUDE_THRESHOLD:
        # print(f"Gyro magnitude triggered at {gyro_magnitude}")
        if abs(gyro_y) > GYRO_PARRY_THRESHOLD:
            print("----- PARRY -----")
            print(f"Gyro y rotation: {abs(gyro_y)}")
            print("------------ End motion ------------")
            last_action_time = current_time  # Update last action time to start cooldown
            return "Parry"
        
        if abs(gyro_x) > GYRO_DASH_THRESHOLD and current_time - last_dash_time > DASH_COOLDOWN_TIME:
            print("----- Dash -----")
            print(f"Gyro x rotation: {abs(gyro_x)}")
            print("------------ End motion ------------")
            last_action_time = current_time  # Update last action time to start cooldown
            last_dash_time = current_time
            direction = "in" if gyro_x < 0 else "out"
            return "Dash " + direction



    return None
