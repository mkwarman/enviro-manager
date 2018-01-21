from probe import Probe
from dht22 import DHT22
from time import sleep
from flask import Flask
from threading import Thread
from duty_cycle import DutyCycle
import RPi_I2C_driver
import gpio
import sys
import sensor
import serial

app = Flask(__name__)

PROBE_DIRECTORY = "/sys/bus/w1/devices/28-0317030193ff/w1_slave"

MAT_TEMP_LOWER_BOUND = 90
MAT_TEMP_TARGET = 93
MAT_TEMP_UPPER_BOUND = 96
AMBIENT_TEMP_LOWER_BOUND = 85
AMBIENT_TEMP_TARGET = 90
AMBIENT_TEMP_UPPER_BOUND = 95
HUMIDITY_UPPER_BOUND = 65
HUMIDITY_LOWER_BOUND = 45

NULL_ZONE = 1

MAT_SERIAL_IDENTIFIER = "M"
LIGHT_SERIAL_IDENTIFIER = "L"
ZERO_CROSS_IDENTIFIER = "Z"

ON = 1
OFF = 0

TEMPERATURE_APPROACH_DELTA_LIMIT = 0.12

display = RPi_I2C_driver.lcd()
probe = Probe(PROBE_DIRECTORY)
dht1_temp = DHT22(gpio.DHT_SENSOR1_PIN, 1)
dht2_humidity = DHT22(gpio.DHT_SENSOR2_PIN, 2)
mat = DutyCycle(MAT_SERIAL_IDENTIFIER)
light = DutyCycle(LIGHT_SERIAL_IDENTIFIER)

mat_enabled = False
light_enabled = True # These two are essentially linked
fogger_enabled = True # at the moment. Disabling one changes nothing

serialConnection = serial.Serial('/dev/serial0', 9600)

poll_sensors = True

display.lcd_display_string("Data:", 1)

probe_temp = 0.0
ambient_temp = 0.0
sensor_values = [
    {
        'temp': 0.0,
        'hum': 0.0
    },
    {
        'temp': 0.0,
        'hum': 0.0
    }
]

if (len(sys.argv) > 1 and sys.argv[1] == 'false'):
    gpio.enabled(False)

def run_probe(probe):
    """
    # Support for multiple probes
    temp = 0

    for probe in probes:
        temp += probe.get_probe_data(probe)

    avg_temp = temp/len(probes)
    """

    temp, display_string = sensor.get_probe_data(probe)
    display.lcd_display_string(display_string, 2)

    if not temp:
        # no useable data
        print("Not enough data to calculate duty cycle!")
        return

    global probe_temp
    previous_temp = probe_temp
    probe_temp = temp

    if temp < MAT_TEMP_TARGET:
        gpio.set_mat(ON)
        if temp < MAT_TEMP_LOWER_BOUND:
            print("Max mat duty cycle")
            mat.max_duty_cycle(serialConnection)
        elif (previous_temp > temp):
            print("Increase mat duty cycle")
            mat.increase_duty_cycle(serialConnection)
        elif (temp - previous_temp > TEMPERATURE_APPROACH_DELTA_LIMIT):
            print("Decrease mat duty cycle due to approach speed")
            mat.decrease_duty_cycle(serialConnection)
    elif temp > MAT_TEMP_TARGET:
        if temp > MAT_TEMP_UPPER_BOUND:
            gpio.set_mat(OFF)
        # Dont mess with duty cycle if state is off
        elif (gpio.mat_state == ON):
            if (previous_temp < temp):
                print("Decrease mat duty cycle")
                mat.decrease_duty_cycle(serialConnection)
            elif (previous_temp - temp > TEMPERATURE_APPROACH_DELTA_LIMIT):
                print("Increase mat duty cycle due to approach speed")
                mat.increase_duty_cycle(serialConnection)

def run_dht_temp(dht):
    global sensor_values

    dht_hum, dht_temp, display_string = sensor.get_dht_data(dht)
    if dht_temp and dht_hum:
        # Only add if sensor returns good data
        sensor_values[dht.number - 1] = {
            'temp': dht_temp,
            'hum': dht_hum
        }
    else:
        print("DHT temp sensor didn't return usable data")
        return

    if display_string:
        display.lcd_display_string(display_string, dht.number + 2)

    global ambient_temp
    previous_ambient_temp = ambient_temp
    ambient_temp = dht_temp

    if ambient_temp < AMBIENT_TEMP_TARGET:
        gpio.set_light(ON)
        if ambient_temp < AMBIENT_TEMP_LOWER_BOUND:
            print("Max light duty cycle")
            light.max_duty_cycle(serialConnection)
        # If temperature falling
        elif (previous_ambient_temp > ambient_temp):
            print("Increase light duty cycle")
            light.increase_duty_cycle(serialConnection)
        elif (ambient_temp - previous_ambient_temp > TEMPERATURE_APPROACH_DELTA_LIMIT):
            print("Decrease light duty cycle due to approach speed")
            light.decrease_duty_cycle(serialConnection)
    elif ambient_temp > AMBIENT_TEMP_TARGET:
        if ambient_temp > AMBIENT_TEMP_UPPER_BOUND:
            gpio.set_light(OFF)
        # Dont mess with duty cycle if state is off
        elif (gpio.light_state == ON):
            if (previous_ambient_temp < ambient_temp):
                print("Decrease light duty cycle")
                light.decrease_duty_cycle(serialConnection)
            elif (previous_ambient_temp - ambient_temp > TEMPERATURE_APPROACH_DELTA_LIMIT):
                print("Increase light duty cycle due to approach speed")
                light.increase_duty_cycle(serialConnection)

def run_dht_humidity(dht):
    global sensor_values

    dht_hum, dht_temp, display_string = sensor.get_dht_data(dht)
    if dht_temp and dht_hum:
        # Only add if sensor returns good data
        sensor_values[dht.number - 1] = {
            'temp': dht_temp,
            'hum': dht_hum
        }
    else:
        print("DHT humidity sensor didn't return usable data")
        return

    if display_string:
        display.lcd_display_string(display_string, dht.number + 2)

    if dht_hum < HUMIDITY_LOWER_BOUND:
        gpio.set_fogger(ON)
        print("Turn on fogger")
    elif dht_hum > HUMIDITY_UPPER_BOUND:
        print("Turn off fogger")
        gpio.set_fogger(OFF)

def poll_sensor_loop():
    while poll_sensors:
        try:
            if (mat_enabled):
                run_probe(probe)
            sleep(.2)
            if (light_enabled):
                run_dht_temp(dht1_temp)
            sleep(.2)
            if (fogger_enabled):
                run_dht_humidity(dht2_humidity)
            sleep(.2)
        except (KeyboardInterrupt, SystemExit):
            print("Stopping...")
            break

    gpio.cleanup()
    display.lcd_clear()
    display.backlight(OFF)

@app.route('/')
@app.route('/index')
def index():
    return "<h1><p>probe temp: {0:0.2f}</br>".format(probe_temp) \
            + "sensor1 (temperature): temp={0:0.2f}F hum={1:0.2f}%</br>".format(sensor_values[0].get('temp'), sensor_values[0].get('hum')) \
            + "sensor2 (humidity): temp={0:0.2f}F hum={1:0.2f}%</p>".format(sensor_values[1].get('temp'), sensor_values[1].get('hum')) \
            + "<p>Mat enabled: " + str(mat_enabled) + " --- Current status: " + ("on" if gpio.mat_state == ON else "off") + "</br>" \
            + "Light enabled: " + str(light_enabled) + " --- Current status: " + ("on" if gpio.light_state == ON else "off") + "</br>" \
            + "Fogger enabled: " + str(fogger_enabled) + " --- Current status: " + ("on" if gpio.fogger_state == ON else "off") + "</br>" \
            + "</p></h1>"

if __name__ == "__main__":
    try:
        process = Thread(target=poll_sensor_loop)
        process.start()
        app.run(host='0.0.0.0', port=80, use_reloader=False)
        process.join(timeout=10)
    except (KeyboardInterrupt, SystemExit):
        print("Stopping...")
        poll_sensors = False

    except Exception as error:
        GPIO.cleanup()
        raise error
