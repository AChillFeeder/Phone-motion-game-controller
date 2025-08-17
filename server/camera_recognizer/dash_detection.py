import cv2
import mediapipe as mp
import numpy as np
from collections import deque

mp_pose = mp.solutions.pose
pose = mp_pose.Pose()
mp_draw = mp.solutions.drawing_utils

# Configurations
DASH_THRESHOLD = 0.06
KNEE_ANGLE_THRESHOLD = 120
JUMP_Y_THRESHOLD = -0.08

# State
hip_history = deque(maxlen=5)
dash_cooldown = 0
jump_cooldown = 0
jump_detected = False
standing_hip_y = None

# Counters
left_dash_count = 0
right_dash_count = 0
jump_count = 0

# Start webcam
cap = cv2.VideoCapture(0)

def get_angle(a, b, c):
    """Calculate the angle at point b between points a and c"""
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)
    radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
    angle = np.abs(radians * 180.0 / np.pi)
    return angle if angle < 180 else 360 - angle

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = pose.process(rgb)

    label = "Standing"

    if dash_cooldown > 0:
        dash_cooldown -= 1
    if jump_cooldown > 0:
        jump_cooldown -= 1

    if results.pose_landmarks:
        landmarks = results.pose_landmarks.landmark
        mp_draw.draw_landmarks(frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

        # Coordinates
        hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP]
        knee = landmarks[mp_pose.PoseLandmark.LEFT_KNEE]
        ankle = landmarks[mp_pose.PoseLandmark.LEFT_ANKLE]

        hip_coords = [hip.x, hip.y]
        knee_coords = [knee.x, knee.y]
        ankle_coords = [ankle.x, ankle.y]

        # 1. Crouch
        knee_angle = get_angle(hip_coords, knee_coords, ankle_coords)
        if knee_angle < KNEE_ANGLE_THRESHOLD:
            label = "Crouching"

        # 2. Dash
        hip_x = hip.x
        hip_history.append(hip_x)
        if len(hip_history) == hip_history.maxlen and dash_cooldown == 0:
            delta = hip_history[-1] - hip_history[0]
            if delta > DASH_THRESHOLD:
                label = "Dash Right"
                right_dash_count += 1
                dash_cooldown = 10
            elif delta < -DASH_THRESHOLD:
                label = "Dash Left"
                left_dash_count += 1
                dash_cooldown = 10

        # 3. Jump
        hip_y = hip.y
        if standing_hip_y is None:
            standing_hip_y = hip_y

        vertical_movement = hip_y - standing_hip_y
        if jump_cooldown == 0 and vertical_movement < JUMP_Y_THRESHOLD:
            label = "Jump!"
            jump_count += 1
            jump_detected = True
            jump_cooldown = 15
        elif jump_detected and vertical_movement > -0.01:
            jump_detected = False
            jump_cooldown = 5

    # HUD
    cv2.putText(frame, label, (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)
    cv2.putText(frame, f"Left Dashes: {left_dash_count}", (30, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 100, 100), 2)
    cv2.putText(frame, f"Right Dashes: {right_dash_count}", (30, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (100, 100, 255), 2)
    cv2.putText(frame, f"Jumps: {jump_count}", (30, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)

    cv2.imshow("Posture Detection", frame)
    if cv2.waitKey(10) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
