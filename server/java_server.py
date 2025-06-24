import socket
import time
from motion_queue_recognizer import recognize

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", 9001))

print("Listening for packets...\n")

def test_delay(timestamp_ms: int, lag_test_flag: str):
    now_ms = int(time.time() * 1000)
    delay_ms = now_ms - timestamp_ms

    if lag_test_flag.lower() == "true":
        print(f"[LAG TEST ON] Round-trip delay: {delay_ms} ms at {time.strftime('%H:%M:%S')}")

    return delay_ms

while True:
    data, _ = sock.recvfrom(1024)
    try:
        decoded = data.decode()
        parts = decoded.strip().split(",")

        if len(parts) == 6:
            sensor_type = parts[0]
            x, y, z = map(float, parts[1:4])
            timestamp = int(parts[4])
            lag_test_flag = parts[5]

            delay = test_delay(timestamp, lag_test_flag)

            action = recognize(sensor_type, x, y, z)
            if action:
                print(f"[ACTION] {action}")

        else:
            print(f"[ERROR] Malformed packet: {decoded}")

    except Exception as e:
        print(f"[EXCEPTION] {e} | Raw: {data}")
