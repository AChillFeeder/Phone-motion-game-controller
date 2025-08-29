# action_bus.py
# Tiny thread-safe pub/sub “bus” for our motion controller.
# Current usage: SensorReceiver -> post_volume_key(...) ; main app subscribes.

from typing import Callable, Any, Dict, List, Tuple
import threading

SubscriberVK = Callable[[str, int], None]                 # (key_code, timestamp_ms)
SubscriberGesture = Callable[[str, Dict[str, Any]], None] # (gesture_name, meta)
SubscriberAction = Callable[[str, Dict[str, Any]], None]  # (action_name, payload)

class ActionBus:
    _lock = threading.Lock()
    _vk_subs: List[SubscriberVK] = []
    _gesture_subs: List[SubscriberGesture] = []
    _action_subs: List[SubscriberAction] = []

    # -------- Volume key (what your SensorReceiver currently uses) --------
    @classmethod
    def on_volume_key(cls, fn: SubscriberVK) -> SubscriberVK:
        """Subscribe to volume-key events. Returns the same fn for easy decoration."""
        with cls._lock:
            cls._vk_subs.append(fn)
        return fn

    @classmethod
    def post_volume_key(cls, key_code: str, timestamp_ms: int) -> None:
        """Publish a volume-key event to all subscribers."""
        with cls._lock:
            subs = list(cls._vk_subs)
        for fn in subs:
            try:
                fn(key_code, timestamp_ms)
            except Exception as e:
                print(f"[ActionBus] volume_key subscriber error: {e}")

    # -------- Optional: gestures (camera/phone recognizers can emit here) --------
    @classmethod
    def on_gesture(cls, fn: SubscriberGesture) -> SubscriberGesture:
        with cls._lock:
            cls._gesture_subs.append(fn)
        return fn

    @classmethod
    def post_gesture(cls, name: str, meta: Dict[str, Any] | None = None) -> None:
        with cls._lock:
            subs = list(cls._gesture_subs)
        meta = meta or {}
        for fn in subs:
            try:
                fn(name, meta)
            except Exception as e:
                print(f"[ActionBus] gesture subscriber error: {e}")

    # -------- Optional: low-level actions (mapped keys/mouse) --------
    @classmethod
    def on_action(cls, fn: SubscriberAction) -> SubscriberAction:
        with cls._lock:
            cls._action_subs.append(fn)
        return fn

    @classmethod
    def post_action(cls, name: str, payload: Dict[str, Any] | None = None) -> None:
        with cls._lock:
            subs = list(cls._action_subs)
        payload = payload or {}
        for fn in subs:
            try:
                fn(name, payload)
            except Exception as e:
                print(f"[ActionBus] action subscriber error: {e}")

    # Utility for tests
    @classmethod
    def clear(cls) -> None:
        with cls._lock:
            cls._vk_subs.clear()
            cls._gesture_subs.clear()
            cls._action_subs.clear()

__all__ = ["ActionBus"]
