# dash_detection.py
import cv2
import mediapipe as mp
import numpy as np
from collections import deque
from typing import Callable, Optional

mp_pose = mp.solutions.pose
mp_draw = mp.solutions.drawing_utils

# Configurations
DASH_THRESHOLD = 0.06           # horizontal hip movement to count as dash
KNEE_ANGLE_THRESHOLD = 120      # below => crouching
JUMP_Y_THRESHOLD = -0.08        # relative hip Y vs baseline for jump
HIP_EMA_ALPHA    = 0.25         # smoothing for hip.y
JUMP_VEL_THR     = 0.015        # need some upward speed to call it a jump
REARM_THR        = -0.01        # must return above this to re-arm

def get_angle(a, b, c):
    """Calculate the angle at point b between points a and c."""
    a = np.array(a); b = np.array(b); c = np.array(c)
    radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
    angle = abs(radians * 180.0 / np.pi)
    return angle if angle < 180 else 360 - angle

def run(on_event: Optional[Callable[[str], None]] = None,
        camera_index: int = 0,
        show_window: bool = True):
    """
    Start webcam-based detection.
    on_event: callback receiving one of {"dash_left","dash_right","jump","crouch"}.
    """
    pose = mp_pose.Pose()
    cap = cv2.VideoCapture(camera_index)

    # State
    hip_history = deque(maxlen=5)
    dash_cooldown = 0
    jump_cooldown = 0
    jump_detected = False
    standing_hip_y = None
    hip_y_ema = None
    hip_y_hist = deque(maxlen=3)

    # Counters (for HUD only)
    left_dash_count = 0
    right_dash_count = 0
    jump_count = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(rgb)

        label = "Standing"
        if dash_cooldown > 0: dash_cooldown -= 1
        if jump_cooldown > 0: jump_cooldown -= 1

        # Defaults for HUD when no pose this frame
        dy = 0.0
        vertical_movement = 0.0

        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark
            mp_draw.draw_landmarks(frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

            # Coordinates (use left side consistently)
            hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP]
            knee = landmarks[mp_pose.PoseLandmark.LEFT_KNEE]
            ankle = landmarks[mp_pose.PoseLandmark.LEFT_ANKLE]

            hip_coords = [hip.x, hip.y]
            knee_coords = [knee.x, knee.y]
            ankle_coords = [ankle.x, ankle.y]

            # 1) Crouch
            knee_angle = get_angle(hip_coords, knee_coords, ankle_coords)
            if knee_angle < KNEE_ANGLE_THRESHOLD:
                label = "Crouching"
                if on_event:
                    on_event("crouch")

            # 2) Dash (left/right) from hip X history
            hip_x = hip.x
            hip_history.append(hip_x)
            if len(hip_history) == hip_history.maxlen and dash_cooldown == 0:
                delta = hip_history[-1] - hip_history[0]
                if delta > DASH_THRESHOLD:
                    label = "Dash Right"
                    right_dash_count += 1
                    dash_cooldown = 10
                    if on_event: on_event("dash_right")
                elif delta < -DASH_THRESHOLD:
                    label = "Dash Left"
                    left_dash_count += 1
                    dash_cooldown = 10
                    if on_event: on_event("dash_left")

            # 3) Jump (EMA of hip Y + velocity gating)
            hip_y = hip.y

            # Smooth hip Y (EMA) and keep short history for velocity
            if hip_y_ema is None:
                hip_y_ema = hip_y
            hip_y_ema = (1.0 - HIP_EMA_ALPHA) * hip_y_ema + HIP_EMA_ALPHA * hip_y
            hip_y_hist.append(hip_y_ema)
            dy = 0.0 if len(hip_y_hist) < 2 else (hip_y_hist[-1] - hip_y_hist[-2])

            # Initialize baseline once we have an EMA
            if standing_hip_y is None:
                standing_hip_y = hip_y_ema

            vertical_movement = hip_y_ema - standing_hip_y

            # Slowly re-center baseline when stable (not jumping/crouching)
            # "Stable" = near baseline and small velocity
            if (not jump_detected) and abs(vertical_movement) < 0.02 and abs(dy) < 0.01 and knee_angle >= KNEE_ANGLE_THRESHOLD:
                standing_hip_y = 0.98 * standing_hip_y + 0.02 * hip_y_ema
                vertical_movement = hip_y_ema - standing_hip_y  # keep consistent with EMA

            # Jump trigger: cooldown + edge (not already jumping) + displacement + upward velocity
            if (jump_cooldown == 0
                and not jump_detected
                and vertical_movement < JUMP_Y_THRESHOLD
                and dy < -JUMP_VEL_THR):
                label = "Jump!"
                jump_count += 1
                jump_detected = True
                jump_cooldown = 15  # ~frame-based

            # Re-arm after returning near baseline and moving downward
            elif jump_detected and vertical_movement > REARM_THR and dy > 0:
                jump_detected = False
                jump_cooldown = max(jump_cooldown, 5)

        # HUD (guard against None on early frames)
        if show_window:
            disp_ema  = hip_y_ema if hip_y_ema is not None else 0.0
            disp_base = standing_hip_y if standing_hip_y is not None else 0.0

            cv2.putText(frame, label, (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)
            cv2.putText(frame, f"Left Dashes: {left_dash_count}", (30, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 100, 100), 2)
            cv2.putText(frame, f"Right Dashes: {right_dash_count}", (30, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (100, 100, 255), 2)
            cv2.putText(frame, f"Jumps: {jump_count}", (30, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)

            cv2.putText(frame, f"hip_y_ema: {disp_ema:.3f}", (30, 220), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200,200,200), 1)
            cv2.putText(frame, f"baseline: {disp_base:.3f}", (30, 245), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200,200,200), 1)
            cv2.putText(frame, f"dy: {dy:.3f}  dY:{vertical_movement:.3f}", (30, 270), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200,200,200), 1)
            cv2.putText(frame, f"cooldown:{jump_cooldown} armed:{not jump_detected}", (30, 295), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200,200,200), 1)

            cv2.imshow("Posture Detection", frame)
            if cv2.waitKey(10) & 0xFF == ord('q'):
                break

    cap.release()
    if show_window:
        cv2.destroyAllWindows()

if __name__ == "__main__":
    def _print_evt(e): print("[CAMERA]", e)
    run(on_event=_print_evt, show_window=True)
