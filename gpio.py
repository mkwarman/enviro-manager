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
    global gpio_enabled
    gpio_enabled = enabled

def set_mat(on_off):
    global mat_state
    if gpio_enabled and mat_state != on_off:
        print("Turning mat " + str(on_off))
        GPIO.output(MAT_RELAY_PIN, on_off)
        mat_state = on_off
    return

def set_light(on_off):
    global light_state
    if gpio_enabled and light_state != on_off:
        print("Turning light " + str(on_off))
        GPIO.output(LIGHT_RELAY_PIN, on_off)
        light_state = on_off
    return

def set_fogger(on_off):
    global fogger_state
    if gpio_enabled and fogger_state != on_off:
        print("Turning fogger " + str(on_off))
        GPIO.output(FOGGER_RELAY_PIN, on_off)
        fogger_state = on_off
    return

def cleanup():
    GPIO.cleanup()
