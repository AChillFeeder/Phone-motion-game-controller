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
