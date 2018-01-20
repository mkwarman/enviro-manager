import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)

MAT_RELAY_PIN = 18
LIGHT_RELAY_PIN = 23
FOGGER_RELAY_PIN = 24

DHT_SENSOR1_PIN = 17
DHT_SENSOR2_PIN = 27

ON = 1
OFF = 0

GPIO.setup(MAT_RELAY_PIN, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(LIGHT_RELAY_PIN, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(FOGGER_RELAY_PIN, GPIO.OUT, initial=GPIO.LOW)

gpio_enabled = True

mat_state = OFF
light_state = OFF
fogger_state = OFF

def enabled(enabled):
    gpio_enabled = enabled

def set_mat(on_off):
    mat_state = on_off
    if gpio_enabled:
        print("Turning mat " + on_off)
        GPIO.output(MAT_RELAY_PIN, on_off)
    return

def set_light(on_off):
    light_state = on_off
    if gpio_enabled:
        print("Turning light " + on_off)
        GPIO.output(LIGHT_RELAY_PIN, on_off)
    return

def set_fogger(on_off):
    fogger_state = on_off
    if gpio_enabled:
        print("Turning fogger " + on_off)
        GPIO.output(FOGGER_RELAY_PIN, on_off)
    return

def cleanup():
    GPIO.cleanup()
