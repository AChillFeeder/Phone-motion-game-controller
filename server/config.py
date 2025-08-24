class Config:
    ENABLE_PHONE = True
    ENABLE_CAMERA = True

    keys = {
        "dash_left": "A",
        "dash_right": "D",
        "jump": "SPACE",
        "crouch": "CTRL",
        "attack": "J",
        "parry": "K",
    }

    # simple conflict policy
    priority = {
        "dash_left": "camera",   # "camera" | "phone"
        "dash_right": "camera",
        "jump": "phone",
        "crouch": "camera",
        "swing": "phone",
        "parry": "phone",
    }

    cooldown_s = {
        "dash_left": 0.12,
        "dash_right": 0.12,
        "jump": 0.18,
        "crouch": 0.10,
        "swing": 0.08,
        "parry": 0.10,
    }

CAMERA_ACTION_MAP = {
    # By default only "jump" maps to an action you already have.
    # Fill these if you want left/right dashes to do something:
    # "dash_left":  "dash_out",   # example
    # "dash_right": "dash_in",    # example
    "jump": "jump",
}


# Configurations
DASH_THRESHOLD = 0.06            # horizontal hip X movement to count as left/right dash
KNEE_ANGLE_THRESHOLD = 120       # below => crouching
JUMP_Y_THRESHOLD = -0.04         # relative hip Y vs baseline for jump
HIP_EMA_ALPHA    = 0.25          # smoothing for hip.y
JUMP_VEL_THR     = 0.015         # need some upward speed to call it a jump
REARM_THR        = -0.01         # must return above this to re-arm

# --- Dash forward specific thresholds (tune for your room/cam) ---
LEAN_Z_THR = -0.15               # shoulders closer than hips by this much (negative = towards camera)
KNEE_MAX_FOR_DF = 140            # both knees should be at/below this angle (bent)
ARM_STRAIGHT_MIN = 150           # elbows ~straight
ARM_BACK_Z_THR = 0.08            # wrists behind hips (greater Z than hips) by this delta
DASH_FWD_COOLDOWN = 12           # frames

# Walking (knee raise)
KNEE_UP_DELTA    = 0.010   # knee must be ~6% of frame height above the hip
KNEE_REARM_DELTA = 0.025   # drop back close to hip before we can trigger again
WALK_COOLDOWN    = 6       # frames to avoid double-firing on jitter

# Dash forward (head low + hands above)
HEAD_LOW_THR      = 0.50   # head (nose) below 70% of frame height (y grows downward)
HAND_ABOVE_MARGIN = 0.02   # hands must be at least this margin above head
HEAD_EMA_ALPHA    = 0.30   # smoothing for head.y

