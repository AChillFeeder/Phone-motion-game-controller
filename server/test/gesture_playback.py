# motion_controller/main.py

from sensor_receiver import SensorReceiver
from dispatcher import SensorDispatcher
from input_handler import InputHandler
from action_bus import ActionBus

# Import recognizers
from recognizers.swing import SwingRecognizer
from recognizers.dash import DashRecognizer
from recognizers.jump import JumpRecognizer

def main():
    print("[Motion Controller] Starting up...")

    # Init dispatcher and action bus
    dispatcher = SensorDispatcher()
    ActionBus.init()

    # Init input handler (binds action -> input)
    input_handler = InputHandler()

    # Register recognizers
    dispatcher.register(SwingRecognizer().handle)
    dispatcher.register(DashRecognizer().handle)
    dispatcher.register(JumpRecognizer().handle)

    # Start sensor receiver
    receiver = SensorReceiver(dispatcher)
    receiver.listen()

if __name__ == "__main__":
    main()
