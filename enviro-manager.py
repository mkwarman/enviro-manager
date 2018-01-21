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
dht1 = DHT22(gpio.DHT_SENSOR1_PIN, 1)
dht2 = DHT22(gpio.DHT_SENSOR2_PIN, 2)
mat = DutyCycle(MAT_SERIAL_IDENTIFIER)
light = DutyCycle(LIGHT_SERIAL_IDENTIFIER)

mat_enabled = False
light_enabled = True # These two are essentially linked
fogger_enabled = True # at the moment. Disabling one changes nothing

serialConnection = serial.Serial('/dev/serial0', 9600)

poll_sensors = True

display.lcd_display_string("Data:", 1)

probe_temp = 0.0
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
ambient_temp = 0.0
ambient_hum = 0.0

if (len(sys.argv) > 1 and sys.argv[1] == 'false'):
    gpio.enabled(False)

def run_probe(probes):
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

def run_dht(dhts):
    # Support for multiple DHTs
    temp = 0
    hum = 0
    sensors = len(dhts)

    global sensor_values

    for index, dht in enumerate(dhts):
        dht_hum, dht_temp, display_string = sensor.get_dht_data(dht)
        if dht_temp and dht_hum:
            # Only add if sensor returns good data
            sensor_values[index] = {
                'temp': dht_temp,
                'hum': dht_hum
            }
            temp += dht_temp
            hum += dht_hum
        else:
            sensors -= 1

        if display_string:
            display.lcd_display_string(display_string, dht.number + 2)

    return # short_circuit

    if sensors < 1:
        # not enough sensors to continue operation
        # TODO: kill relay?
        print("Not enough sensors to calculate duty cycle!")
        return

    avg_temp = temp/sensors
    avg_hum = hum/sensors

    global ambient_temp
    global ambient_hum
    previous_temp = ambient_temp
    #previous_hum = ambient_hum #unused
    ambient_temp = avg_temp
    ambient_hum = avg_hum

    if avg_hum < HUMIDITY_LOWER_BOUND:
        gpio.set_fogger(ON)
        print("Turn on fogger")
    elif avg_hum > HUMIDITY_UPPER_BOUND:
        print("Turn off fogger")
        gpio.set_fogger(OFF)

    if avg_temp < AMBIENT_TEMP_TARGET:
        gpio.set_light(ON)
        if avg_temp < AMBIENT_TEMP_LOWER_BOUND:
            print("Max light duty cycle")
            light.max_duty_cycle(serialConnection)
        elif (previous_temp > avg_temp):
            print("Increase light duty cycle")
            light.increase_duty_cycle(serialConnection)
        elif (avg_temp - previous_temp > TEMPERATURE_APPROACH_DELTA_LIMIT):
            print("Decrease light duty cycle due to approach speed")
            mat.decrease_duty_cycle(serialConnection)
    elif avg_temp > AMBIENT_TEMP_TARGET:
        if avg_temp > AMBIENT_TEMP_UPPER_BOUND:
            gpio.set_light(OFF)
        # Dont mess with duty cycle if state is off
        elif (gpio.light_state == ON):
            if (previous_temp < avg_temp):
                print("Decrease light duty cycle")
                light.decrease_duty_cycle(serialConnection)
            elif (previous_temp - avg_temp > TEMPERATURE_APPROACH_DELTA_LIMIT):
                print("Increase light duty cycle due to approach speed")
                light.increase_duty_cycle(serialConnection)

def poll_sensor_loop():
    while poll_sensors:
        try:
            if (probe_enabled):
                run_probe([probe])
            #sleep(.1)
            if (light_enabled or fogger_enabled):
                run_dht([dht1, dht2])
            #sleep(.1)
        except (KeyboardInterrupt, SystemExit):
            print("Stopping...")
            break

    gpio.cleanup()
    display.lcd_clear()
    display.backlight(OFF)

@app.route('/live')
def live():
    #return "value: " + str(executed)
    return "<h1>probe temp: {0:0.2f}</br>".format(probe_temp) \
            + "sensor1: temp={0:0.2f}F hum={1:0.2f}%</br>".format(sensor_values[0].get('temp'), sensor_values[0].get('hum')) \
            + "sensor2: temp={0:0.2f}F hum={1:0.2f}%</h1>".format(sensor_values[1].get('temp'), sensor_values[1].get('hum'))

if __name__ == "__main__":
    try:
        process = Thread(target=poll_sensor_loop)
        process.start()
        app.run(host='0.0.0.0', port=80, use_reloader=False)
        process.join(timeout=10)
    except (KeyboardInterrupt, SystemExit):
        print("Stopping...")
        poll_sensors = False
