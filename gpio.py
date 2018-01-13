import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)

#GPIO.setup(17, OUTPUT)
#GPIO.setup(27, OUTPUT)
#GPIO.setup(22, OUTPUT)

def setup_pin(pin):
    GPIO.setup(pin, GPIO.OUT)

def set_high(pin):
    GPIO.output(pin, 1)

def set_low(pin):
    GPIO.output(pin, 0)

def cleanup():
    GPIO.cleanup()
