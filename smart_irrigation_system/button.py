import RPi.GPIO as GPIO
import time
from smart_irrigation_system.logger import get_logger

class Button:
    def __init__(self, gpio_pin, led_pin=None):
        self.gpio_pin = gpio_pin
        self.led_pin = led_pin
        self.state = False  # software state (False = off, True = on)
        self.logger = get_logger(f"Button-{gpio_pin}")
        
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.gpio_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
        if self.led_pin is not None:
            GPIO.setup(self.led_pin, GPIO.OUT)
            GPIO.output(self.led_pin, GPIO.LOW)
        
        # Interrupt for button press (detecting falling edge)
        GPIO.add_event_detect(self.gpio_pin, GPIO.FALLING, callback=self._handle_press, bouncetime=200)
        
    def _handle_press(self, channel):
        # Toggle softwarove state
        self.state = not self.state
        
        # Indicate state change on LED if it is set
        if self.led_pin is not None:
            GPIO.output(self.led_pin, GPIO.HIGH if self.state else GPIO.LOW)
        
        # Log the state change
        self.logger.info(f"Button on GPIO {self.gpio_pin} pressed. New state: {'ON' if self.state else 'OFF'}")
        
    def is_pressed(self):
        # True if the button is pressed (GPIO pin is LOW)
        return GPIO.input(self.gpio_pin) == GPIO.LOW
    
    def get_state(self):
        # Get the current software state of the button
        return self.state
    
    def cleanup(self):
        # Call this method to clean up GPIO settings
        GPIO.cleanup([self.gpio_pin, self.led_pin] if self.led_pin is not None else [self.gpio_pin])

