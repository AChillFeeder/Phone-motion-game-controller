import pydirectinput
import time

class InputHandler:
    def __init__(self):
        self.actions = {
            "parry": self._right_click,
            "attack": self._left_click,
            "jump": self._press_space,
            "reset_position": self._custom_reset_behavior,
            "combat_art": self._combat_art,
            "dash_in": lambda: self._dash("w"),
            "dash_out": lambda: self._dash("s"),
        }

    def handle(self, action: str):
        cmd = self.actions.get(action.lower())
        if cmd:
            cmd()
        else:
            print(f"[WARN] Unknown action: {action}")

    # --- Keyboard actions ---

    def _press_space(self):
        pydirectinput.press('space')

    def _dash(self, key):
        pydirectinput.keyDown(key)
        pydirectinput.keyDown('shift')
        time.sleep(0.02)
        pydirectinput.keyUp(key)
        pydirectinput.keyUp('shift')

    def _combat_art(self):
        pydirectinput.mouseDown(button='right')
        pydirectinput.mouseDown(button='left')
        pydirectinput.mouseUp(button='left')
        pydirectinput.mouseUp(button='right')

    # --- Mouse actions ---

    def _left_click(self):
        pydirectinput.mouseDown(button='left')
        pydirectinput.mouseUp(button='left')

    def _right_click(self):
        pydirectinput.mouseDown(button='right')
        pydirectinput.mouseUp(button='right')

    def _custom_reset_behavior(self):
        print("[Action] Resetting virtual position (custom logic here)")
