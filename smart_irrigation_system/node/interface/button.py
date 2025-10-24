try:
    import RPi.GPIO as GPIO
    GPIO_SUPPORTED = True
# if ImportError or RuntimeError occurs, we will use a dummy GPIO class for testing
except (ImportError, RuntimeError):
    GPIO_SUPPORTED = False
    class GPIO:
        BCM = None
        IN = None
        OUT = None
        PUD_UP = None
        LOW = None
        HIGH = None
        FALLING = None
        RISING = None
        BOTH = None
        @staticmethod
        def setmode(mode): pass
        @staticmethod
        def setup(pin, mode, pull_up_down=None): pass
        @staticmethod
        def output(pin, state): pass
        @staticmethod
        def input(pin): return False
        @staticmethod
        def add_event_detect(pin, edge, callback=None, bouncetime=None): pass
        @staticmethod
        def cleanup(pins=None): pass
    
    GPIO = GPIO  # Use the dummy GPIO class for testing

import time
from smart_irrigation_system.node.utils.logger import get_logger

class Button:
    def __init__(self, gpio_pin, led_pin=None, user_callback=None):
        self.gpio_pin = gpio_pin
        self.led_pin = led_pin
        self.state = False  # software state (False = off, True = on)
        self.user_callback = user_callback  
        self.logger = get_logger(f"Button-{gpio_pin}")
        
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.gpio_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
        if self.led_pin is not None:
            GPIO.setup(self.led_pin, GPIO.OUT)
            GPIO.output(self.led_pin, GPIO.LOW)
        
        # Interrupt for button press (detecting falling edge)
        GPIO.add_event_detect(self.gpio_pin, GPIO.FALLING, callback=self._handle_press, bouncetime=200)
        
        if GPIO_SUPPORTED:
            self.logger.info(f"Button initialized on GPIO {self.gpio_pin} with LED on GPIO {self.led_pin if self.led_pin else 'None'}")
        else:
            self.logger.warning(f"Button initialized, but GPIO support is not available. Using dummy GPIO.")
        
    def _handle_press(self, channel):
        # Toggle softwarove state
        self.state = not self.state
        
        # Indicate state change on LED if it is set
        if self.led_pin is not None:
            GPIO.output(self.led_pin, GPIO.HIGH if self.state else GPIO.LOW)
        
        # Log the state change
        self.logger.info(f"Button on GPIO {self.gpio_pin} pressed. New state: {'ON' if self.state else 'OFF'}")

        if self.user_callback:
            try:
                self.user_callback(self.state)
            except Exception as e:
                self.logger.error(f"Error in user callback: {e}")
        
    def is_pressed(self):
        # True if the button is pressed (GPIO pin is LOW)
        return GPIO.input(self.gpio_pin) == GPIO.LOW
    
    def get_state(self):
        # Get the current software state of the button
        return self.state
    
    def cleanup(self):
        # Call this method to clean up GPIO settings
        GPIO.cleanup([self.gpio_pin, self.led_pin] if self.led_pin is not None else [self.gpio_pin])

