# motion_controller/sensor_receiver.py

import socket
import threading
from action_bus import ActionBus

class SensorReceiver:
    def __init__(self, dispatcher, host="0.0.0.0", port=9001):
        self.dispatcher = dispatcher
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def listen(self):
        self.sock.bind((self.host, self.port))
        print(f"[SensorReceiver] Listening on {self.host}:{self.port}")

        thread = threading.Thread(target=self._receive_loop, daemon=True)
        thread.start()
        thread.join()  # Block main thread

    def _receive_loop(self):
        while True:
            try:
                data, _ = self.sock.recvfrom(1024)
                decoded = data.decode().strip()
                parts = decoded.split(",")

                sensor_type = parts[0].lower()
                if sensor_type == "volkey" and len(parts) == 3:
                    ActionBus.post_volume_key(parts[1], int(parts[2]))
                else:
                    self.dispatcher.dispatch(sensor_type, parts)

            except Exception as e:
                print(f"[SensorReceiver] Error: {e}")
