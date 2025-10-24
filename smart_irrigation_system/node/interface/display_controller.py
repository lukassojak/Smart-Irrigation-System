# use pip install luma.oled to install the library
# on raspberry pi allow i2c interface in raspi-config
import time
from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306
from luma.core.render import canvas
from PIL import ImageFont
from datetime import datetime

from smart_irrigation_system.node.core.irrigation_controller import IrrigationController


ADDRESS = 0x3C  # I2C address for the OLED display, most of ssd1306 displays use this address

# Mock I2C interface for testing purposes on non-Raspberry Pi environments
class MockI2C:
    def __init__(self, port, address):
        # print(f"Mock I2C initialized with port={port}, address={address}")
        pass

    def cleanup(self):
        # print("Mock I2C cleanup called")
        pass
    
    def command(self, *cmd):
        # print(f"Mock I2C command called with: {cmd}")
        pass
    
    def data(self, data):
        # print(f"Mock I2C data called with: {data}")
        pass

# It is necessary to update the display in main loop by calling `display_controller.render()`
# It is necessary to add button callback to switch modes by calling `display_controller.next_mode()`
# Implement interface to the IrrigationController to get necessary data for rendering
class DisplayController:
    def __init__(self, irrigation_controller):
        # for running on Non-Raspberry Pi environment, we will use a dummy interface
        try:
            self.serial = i2c(port=1, address=ADDRESS)
        except Exception:
            print("Could not find I2C device. Using dummy interface for testing.")
            self.serial = MockI2C(port=1, address=ADDRESS)

        self.device = ssd1306(self.serial, width=128, height=32, rotate=0)
        self.font = ImageFont.load_default()

        self.i_c: IrrigationController = irrigation_controller

        self.modes = ['dashboard', 'last_irrigation', 'current_irrigation']
        self.current_mode_index = -1    # -1 means display is off
        self.display_timeout = 10       # seconds before display turns off
        self.last_mode_switch_time = None

    
    def next_mode(self):
        self.current_mode_index = (self.current_mode_index + 1) % len(self.modes)
        self.last_mode_switch_time = time.time()
        self.render()


    def render(self):
        # If the display is off, do not render anything
        if self.current_mode_index == -1:
            self.clear()
            return
        
        # Automatically turn off the display after a timeout
        if self.last_mode_switch_time and (time.time() - self.last_mode_switch_time) > self.display_timeout:
            self.current_mode_index = -1
            self.clear()
            return

        current_mode = self.modes[self.current_mode_index]

        with canvas(self.device) as draw:
            if current_mode == 'dashboard':
                self._render_dashboard(draw)
            elif current_mode == 'last_irrigation':
                self._render_last_irrigation(draw)
            elif current_mode == 'current_irrigation':
                self._render_current_irrigation(draw)

    def _render_dashboard(self, draw):
        state = self.i_c.get_state()        # 'IDLE', 'IRRIGATING', 'ERROR'
        warnings = self.i_c.get_warnings()  # Number of warnings
        errors = self.i_c.get_errors()      # Number of errors

        # Upper section: Warnings and Errors
        draw.text((0, 0), f"Warnings: {warnings}", font=self.font, fill=255)    # 255 - white color
        draw.text((80, 0), f"Errors: {errors}", font=self.font, fill=255)

        # Main section: Current state of the Irrigation Controller
        draw.text((30, 12), f"State: {state}", font=self.font, fill=255)

        if state == 'IRRIGATING':
            # Lower section: IDs of currently irrigating circuits
            active_circuits = self.i_c.get_running_circuits()           # List of circuit IDs
            circuits_str = " ".join(str(c) for c in active_circuits)    # Example: "1 2 3"
            draw.text((30, 24), f"Circuits: {circuits_str}", font=self.font, fill=255)
    
    def _render_last_irrigation(self, draw):
        last_irrigation = self.i_c.get_last_irrigation_datetime()  # Get last irrigation datetime
        if last_irrigation:
            last_irrigation_str = last_irrigation.strftime("%Y-%m-%d %H:%M:%S")
        else:
            last_irrigation_str = "No last irrigation data"
        
        draw.text((10, 0), "Last Irrigation:", font=self.font, fill=255)

        # Get all circuit IDs in the controller
        circuits = self.i_c.get_circuits()          # List of circuit IDs

        # Display last irrigation volume in liters for each circuit in 2 columns
        for i, circuit_id in enumerate(circuits):
            volume = self.i_c.get_last_irrigation_volume(circuit_id)
            volume_str = f"{circuit_id}: {volume}L" if volume is not None else f"{circuit_id}: No data"
            x = (i % 2) * 64
            y = 12 + ((i // 2) * 10)
            draw.text((x, y), volume_str, font=self.font, fill=255)
        
    def _render_current_irrigation(self, draw):
        mode = "SEQ" if self.i_c.is_sequential_mode() else "CONC"
        flow = self.i_c.get_current_flow()

        draw.text((0, 0), f"Mode:{mode}", font=self.font, fill=255)
        draw.text((80, 0), f"Flow:{flow} L/min", font=self.font, fill=255)

        if self.i_c.is_irrigating():
            draw.text((10, 10), "Irrigating ...", font=self.font, fill=255)

            active_circuits = self.i_c.get_running_circuits()  # List of circuit IDs
            # here get waiting circuits when the interface is present
            # placeholder
            waiting_circuits = "Unsupported"

            draw.text((0, 20), "A: " + ' '.join(str(c) for c in active_circuits), font=self.font, fill=255)
            draw.text((0, 30), "W: " + waiting_circuits, font=self.font, fill=255)
        else:
            next_time = self.i_c.get_next_irrigation_time()         # expected datetime.datetime
            formatted_time = next_time.strftime("%d.%m. %H:%M") if next_time else "No next irrigation"
            draw.text((5, 14), f"Next: {formatted_time}", font=self.font, fill=255)


    def clear(self):
        self.device.clear()
        self.device.show()

    def cleanup(self):
        """Cleanup method to release resources."""
        self.device.cleanup()
        self.clear()
        self.current_mode_index = -1
        self.last_mode_switch_time = None