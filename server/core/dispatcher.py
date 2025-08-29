# motion_controller/dispatcher.py

class SensorDispatcher:
    def __init__(self):
        self.recognizers = []  # List of recognizer callbacks

    def register(self, recognizer_callback):
        """
        Register a callback that takes (sensor_type, data: dict)
        """
        self.recognizers.append(recognizer_callback)

    def dispatch(self, sensor_type, data):
        """
        Dispatch parsed sensor data to all registered recognizers.
        :param sensor_type: 'gyro', 'accel', 'rotq', etc.
        :param data: Dictionary with x/y/z or quaternion data
        """
        for recognizer in self.recognizers:
            recognizer(sensor_type, data)
