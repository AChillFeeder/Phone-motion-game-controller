import math
import time

# Thresholds
ACCEL_START_THRESHOLD = 2  # Minimum acceleration to start tracking motion
ACCEL_STOP_THRESHOLD = 2   # Acceleration threshold to stop tracking
DISTANCE_SLASH_THRESHOLD = 40  # Minimum total distance to consider it a slash
COOLDOWN_TIME = 0.5  # Minimum time between actions
NUMBER_OF_RECORDS_IN_MOTION_THRESHOLD = 6
GYRO_PARRY_THRESHOLD = 8  # Angular velocity threshold for detecting a parry (wrist twist)

# State variables
last_action_time = 0  # Stores the time of the last action
tracking_motion = False
initial_time = 0

action_total_velocity = 0
number_of_records_in_motion = 0

def recognize_movement(data):
    global last_action_time, tracking_motion, initial_time, action_total_velocity, number_of_records_in_motion
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

    # Time step (delta time) between readings (assuming consistent 1ms intervals)
    dt = 0.001  # Adjust this to match your actual sensor update rate

    # Start tracking motion if acceleration exceeds the start threshold
    if accel_magnitude > ACCEL_START_THRESHOLD and not tracking_motion:
        tracking_motion = True
        print("------------ motion start ------------")
        action_total_velocity = 0
        number_of_records_in_motion = 0

    # Continue tracking motion if we're in the tracking state
    if tracking_motion:
        action_total_velocity += accel_magnitude
        number_of_records_in_motion += 1

        # Stop tracking if acceleration falls below the stop threshold
        if accel_magnitude < ACCEL_STOP_THRESHOLD:
            tracking_motion = False

            # Determine if it's a slash, dash, or parry
            if action_total_velocity > DISTANCE_SLASH_THRESHOLD:
                tracking_motion = False
                print("Slash detected!")
                print(f"Total displacement: {action_total_velocity}")
                print(f"Total number of motions: {number_of_records_in_motion}")
                print("------------ End motion ------------")
                last_action_time = current_time  # Update last action time to start cooldown
                return "Attack"

            elif number_of_records_in_motion < NUMBER_OF_RECORDS_IN_MOTION_THRESHOLD and number_of_records_in_motion > 2:
                print(f"Dash detected")
                print(f"Total displacement: {action_total_velocity}")
                print(f"Total number of motions: {number_of_records_in_motion}")
                print(f"Gyro x rotation: {abs(gyro_x)}")
                print("------------ End motion ------------")
                last_action_time = current_time  # Update last action time to start cooldown
                return "Dash"
                
    # Separate parry detection logic using gyroscope
    if gyro_magnitude > 8:
        # print(f"Gyro magnitude triggered at {gyro_magnitude}")
        if abs(gyro_y) > GYRO_PARRY_THRESHOLD:
            print("----- PARRY -----")
            print(f"Gyro y rotation: {abs(gyro_y)}")
            print("------------ End motion ------------")
            last_action_time = current_time  # Update last action time to start cooldown
            return "Parry"

    return None
