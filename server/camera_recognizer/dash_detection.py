# dash_detection.py
import cv2
import mediapipe as mp
import numpy as np
from collections import deque
from typing import Callable, Optional
from config import *

mp_pose = mp.solutions.pose
mp_draw = mp.solutions.drawing_utils



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
    on_event: callback receiving one of {"dash_left","dash_right","dash_forward","jump","crouch"}.
    """
    pose = mp_pose.Pose()
    cap = cv2.VideoCapture(camera_index)

    # State
    hip_history = deque(maxlen=5)
    jump_detected = False
    standing_hip_y = None
    hip_y_ema = None
    hip_y_hist = deque(maxlen=3)
    knee_up_active_L = False
    knee_up_active_R = False
    head_y_ema = None

    # Cooldowns
    dash_cooldown = 0
    jump_cooldown = 0
    dash_fwd_cooldown = 0
    walk_cooldown = 0

    # Counters (for HUD only)
    steps_count = 0
    left_dash_count = 0
    right_dash_count = 0
    jump_count = 0
    dash_fwd_count = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(rgb)

        label = "Standing"
        if dash_cooldown > 0: dash_cooldown -= 1
        if dash_fwd_cooldown > 0: dash_fwd_cooldown -= 1
        if jump_cooldown > 0: jump_cooldown -= 1
        if walk_cooldown > 0: walk_cooldown -= 1


        # Defaults for HUD when no pose this frame
        dy = 0.0
        vertical_movement = 0.0

        if results.pose_landmarks:
            lm = results.pose_landmarks.landmark
            mp_draw.draw_landmarks(frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

            # Landmarks (both sides where needed)
            LHIP = lm[mp_pose.PoseLandmark.LEFT_HIP]
            RHIP = lm[mp_pose.PoseLandmark.RIGHT_HIP]
            LKN  = lm[mp_pose.PoseLandmark.LEFT_KNEE]
            RKN  = lm[mp_pose.PoseLandmark.RIGHT_KNEE]
            LAN  = lm[mp_pose.PoseLandmark.LEFT_ANKLE]
            RAN  = lm[mp_pose.PoseLandmark.RIGHT_ANKLE]
            LSH  = lm[mp_pose.PoseLandmark.LEFT_SHOULDER]
            RSH  = lm[mp_pose.PoseLandmark.RIGHT_SHOULDER]
            LEL  = lm[mp_pose.PoseLandmark.LEFT_ELBOW]
            REL  = lm[mp_pose.PoseLandmark.RIGHT_ELBOW]
            LWR  = lm[mp_pose.PoseLandmark.LEFT_WRIST]
            RWR  = lm[mp_pose.PoseLandmark.RIGHT_WRIST]

            # 1) Crouch (left leg angle as quick proxy)
            knee_angle_left = get_angle([LHIP.x,LHIP.y],[LKN.x,LKN.y],[LAN.x,LAN.y])
            if knee_angle_left < KNEE_ANGLE_THRESHOLD:
                label = "Crouching"
                if on_event: on_event("crouch")

            # 2) Dash left/right from hip X history
            hip_x = LHIP.x  # choose one side consistently
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
            hip_y = LHIP.y
            if hip_y_ema is None:
                hip_y_ema = hip_y
            hip_y_ema = (1.0 - HIP_EMA_ALPHA) * hip_y_ema + HIP_EMA_ALPHA * hip_y
            hip_y_hist.append(hip_y_ema)
            dy = 0.0 if len(hip_y_hist) < 2 else (hip_y_hist[-1] - hip_y_hist[-2])

            if standing_hip_y is None:
                standing_hip_y = hip_y_ema

            vertical_movement = hip_y_ema - standing_hip_y

            # re-center baseline when stable (not crouching, not jumping)
            if (not jump_detected) and abs(vertical_movement) < 0.02 and abs(dy) < 0.01 and knee_angle_left >= KNEE_ANGLE_THRESHOLD:
                standing_hip_y = 0.98 * standing_hip_y + 0.02 * hip_y_ema
                vertical_movement = hip_y_ema - standing_hip_y

            if (jump_cooldown == 0
                and not jump_detected
                and vertical_movement < JUMP_Y_THRESHOLD
                and dy < -JUMP_VEL_THR):
                label = "Jump!"
                jump_count += 1
                jump_detected = True
                jump_cooldown = 15
            elif jump_detected and vertical_movement > REARM_THR and dy > 0:
                jump_detected = False
                jump_cooldown = max(jump_cooldown, 5)

            # 4) Dash Forward (new: head low + both hands above head)
            # Landmarks we need
            NOSE = lm[mp_pose.PoseLandmark.NOSE]
            LWR  = lm[mp_pose.PoseLandmark.LEFT_WRIST]
            RWR  = lm[mp_pose.PoseLandmark.RIGHT_WRIST]

            # Smooth head Y for robustness
            if head_y_ema is None:
                head_y_ema = NOSE.y
            head_y_ema = (1.0 - HEAD_EMA_ALPHA) * head_y_ema + HEAD_EMA_ALPHA * NOSE.y

            head_low    = head_y_ema > HEAD_LOW_THR
            hands_above = (LWR.y < head_y_ema - HAND_ABOVE_MARGIN) and (RWR.y < head_y_ema - HAND_ABOVE_MARGIN)

            if dash_fwd_cooldown == 0 and head_low and hands_above:
                label = "Dash Forward"
                dash_fwd_count += 1
                dash_fwd_cooldown = DASH_FWD_COOLDOWN
                if on_event: on_event("dash_forward")


            # 5) Walking / Knee Up (either leg)
            # y grows downward in MediaPipe, so (hip.y - knee.y) > 0 means knee is above hip.
            diffL = LHIP.y - LKN.y
            diffR = RHIP.y - RKN.y

            if walk_cooldown == 0:
                if not knee_up_active_L and diffL > KNEE_UP_DELTA:
                    label = "Walk (L)"
                    steps_count += 1
                    knee_up_active_L = True
                    walk_cooldown = WALK_COOLDOWN
                    if on_event: on_event("walk_step")

                elif not knee_up_active_R and diffR > KNEE_UP_DELTA:
                    label = "Walk (R)"
                    steps_count += 1
                    knee_up_active_R = True
                    walk_cooldown = WALK_COOLDOWN
                    if on_event: on_event("walk_step")

            # Re-arm when knee comes back near hip height
            if knee_up_active_L and diffL < KNEE_REARM_DELTA:
                knee_up_active_L = False
            if knee_up_active_R and diffR < KNEE_REARM_DELTA:
                knee_up_active_R = False


        # HUD
        if show_window:
            disp_ema  = hip_y_ema if hip_y_ema is not None else 0.0
            disp_base = standing_hip_y if standing_hip_y is not None else 0.0

            cv2.putText(frame, label, (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)
            cv2.putText(frame, f"Left Dashes: {left_dash_count}", (30, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 100, 100), 2)
            cv2.putText(frame, f"Right Dashes: {right_dash_count}", (30, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (100, 100, 255), 2)
            cv2.putText(frame, f"Jumps: {jump_count}", (30, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
            cv2.putText(frame, f"Dash Fwd: {dash_fwd_count}", (30, 220), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
            cv2.putText(frame, f"Steps: {steps_count}", (30, 200),
            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 200, 255), 2)

            cv2.putText(frame, f"hip_y_ema: {disp_ema:.3f}", (30, 260), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200,200,200), 1)
            cv2.putText(frame, f"baseline: {disp_base:.3f}", (30, 282), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200,200,200), 1)
            cv2.putText(frame, f"dy: {dy:.3f}  dY:{vertical_movement:.3f}", (30, 304), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200,200,200), 1)
            cv2.putText(frame, f"head_y: { (head_y_ema or 0):.3f}  thr:{HEAD_LOW_THR:.2f}",
                (30, 326), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200,200,200), 1)
            try:
                cv2.putText(frame, f"Lw:{LWR.y:.3f} Rw:{RWR.y:.3f} > above:{(head_y_ema - HAND_ABOVE_MARGIN):.3f}",
                    (30, 348), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200,200,200), 1)
            except UnboundLocalError:
                pass

            cv2.imshow("Posture Detection", frame)
            if cv2.waitKey(10) & 0xFF == ord('q'):
                break

    cap.release()
    if show_window:
        cv2.destroyAllWindows()

if __name__ == "__main__":
    def _print_evt(e): print("[CAMERA]", e)
    run(on_event=_print_evt, show_window=True)
