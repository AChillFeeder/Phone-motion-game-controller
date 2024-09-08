import math
import time
import pygame
import threading

# Thresholds for detecting different movements
GYRO_ATTACK_THRESHOLD = 2.0  # Angular velocity for slashes (rad/s)
ACCEL_ATTACK_THRESHOLD = 4  # Acceleration for slashes (G-force)
ACCEL_PARRY_Z_THRESHOLD = -0.7  # Z-axis threshold to detect screen facing the floor (m/s²)
ACCEL_DASH_THRESHOLD = 1.0  # Acceleration for dash (G-force)
ACCEL_DASH_X_THRESHOLD = 2.0  # Quick tilt on X-axis for left/right dash (G-force)
ACCEL_DASH_Y_THRESHOLD = 1.5  # Quick tilt on Y-axis for forward dash (G-force)
BACK_FLICK_THRESHOLD = -1.5  # Backward flick on Y-axis to enter dash mode
DASH_MODE_TIMEOUT = 3.0  # Timeout for dash mode in seconds

dash_mode = False
dash_mode_start_time = 0

# Cooldown between movements to avoid multiple detections for a single action
COOLDOWN_TIME = 0.3
last_action_time = 0



def recognize_movement(data):
    global last_action_time, dash_mode, dash_mode_start_time
    
    current_time = time.time()
    dash_activated = False

    # Extract gyroscope and accelerometer data
    gyro_x = data['gyroscope']['x']
    gyro_y = data['gyroscope']['y']
    gyro_z = data['gyroscope']['z']

    accel_x = data['accelerometer']['x']
    accel_y = data['accelerometer']['y']
    accel_z = data['accelerometer']['z']

    # Calculate the magnitude of the accelerometer and gyroscope vectors
    accel_magnitude = math.sqrt(accel_x**2 + accel_y**2 + accel_z**2)
    gyro_magnitude = math.sqrt(gyro_x**2 + gyro_y**2 + gyro_z**2)

    # Attack detection (slash down or to the side)
    # if gyro_magnitude > GYRO_ATTACK_THRESHOLD or accel_magnitude > ACCEL_ATTACK_THRESHOLD:
    if accel_magnitude > ACCEL_ATTACK_THRESHOLD and gyro_magnitude < 10 and not dash_mode:
        if current_time - last_action_time > COOLDOWN_TIME:
            last_action_time = current_time
            print('\n\n------------------ ATTACK DATA ----------------')
            print("gyro_magnitude: ", gyro_magnitude)
            print("accel_magnitude: ", accel_magnitude)
            return "Attack"

    # Parry detection (screen facing the floor)
    # If the phone's Z-axis acceleration is strongly negative, we detect a parry
    if gyro_magnitude > 5 and accel_magnitude < 4 and gyro_y > 8:
        if current_time - last_action_time > COOLDOWN_TIME:
            print('\n\n------------------ PARRY DATA ----------------')
            print("gyro Z: ", gyro_z)
            last_action_time = current_time
            return "Parry"
        else:
            print('\n\n------------------ PARRY COOLDOWN ----------------')

    # Enter Dash Mode: Backward flick detected on Y-axis
    if accel_y < BACK_FLICK_THRESHOLD and not dash_mode and dash_activated:
        dash_mode = True
        dash_mode_start_time = current_time
        print("\n\n! DASHMODE ENTERED !")
        print("accel_y: ", accel_y)
        print("gyro_y: ", gyro_y)

        pygame.mixer.init()
        pygame.mixer.music.load('C:/Users/Reda/Desktop/PhoneGameController/dash_mode.mp3')

        threading.Thread(target=pygame.mixer.music.play(), daemon=True).start()
        # playsound("C:/Users/Reda/Desktop/PhoneGameController/dash_mode.mp3") 
        return "Dash Mode Entered"

    # Dash mode active: Detect direction (left, right, forward)
    if dash_mode:
        # Check for directional dashing
        if abs(accel_x) > ACCEL_DASH_X_THRESHOLD or abs(accel_y) > ACCEL_DASH_Y_THRESHOLD:
            if current_time - last_action_time > COOLDOWN_TIME:
                last_action_time = current_time
                dash_mode = False  # Exit dash mode after dash
                print('\n\n------------------ DASH ----------------')
                return "Dash"

        # Exit dash mode if no dash is performed within the timeout period
        if current_time - dash_mode_start_time > DASH_MODE_TIMEOUT:
            dash_mode = False
            print("\n\n~~ DASH MODE TIMEOUT ~~")
    return None  # No movement detected or recognized
