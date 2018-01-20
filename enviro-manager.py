from sensor import Probe, DHT22
from time import sleep
from app import app
from multiprocessing import Process
import RPi_I2C_driver
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)

PROBE_DIRECTORY = "/sys/bus/w1/devices/28-0317030193ff/w1_slave"

MAT_TEMP_LOWER_BOUND = 90
MAT_TEMP_UPPER_BOUND = 95
AMBIENT_TEMP_LOWER_BOUND = 84
AMBIENT_TEMP_UPPER_BOUND = 86
HUMIDITY_UPPER_BOUND = 60
HUMIDITY_LOWER_BOUND = 40

MAT_RELAY_PIN = 18
LIGHT_RELAY_PIN = 23
FOGGER_RELAY_PIN = 24

GPIO.setup(MAT_RELAY_PIN, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(LIGHT_RELAY_PIN, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(FOGGER_RELAY_PIN, GPIO.OUT, initial=GPIO.LOW)

ON = 1
OFF = 0

display = RPi_I2C_driver.lcd()
probe = Probe(PROBE_DIRECTORY)
dht1 = DHT22(17, 1)
dht2 = DHT22(27, 2)

display.lcd_display_string("Data:", 1)

def set_mat(on_off):
    GPIO.output(MAT_RELAY_PIN, on_off)
    return

def set_light(on_off):
    GPIO.output(LIGHT_RELAY_PIN, on_off)
    return

def set_fogger(on_off):
    GPIO.output(FOGGER_RELAY_PIN, on_off)
    return

def get_probe_data(probe):
    if probe.disabled:
        display.lcd_display_string(probe.disabled_string, 2)
        return
    
    try:
        temp = probe.get_temp_f()
    
    except (RuntimeError, IOError) as error:
        # TODO: Handle error - ALARM
        display.lcd_display_string("Check probe conn!", 2)
        print("Exception while polling probe: " + str(error))
        return

    display.lcd_display_string("Probe Temp: {0:0.2f}F".format(temp), 2)
    
    return temp

def run_probe(probes):
    """
    # Support for multiple probes
    temp = 0

    for probe in probes:
        temp += probe.get_probe_data(probe)

    avg_temp = temp/len(probes)
    """

    temp = get_probe_data(probe)

    if not temp:
        # no useable data
        print("Not enough data to calculate duty cycle!")
        return

    if temp < MAT_TEMP_LOWER_BOUND:
        # increase mat duty cycle
        set_mat(ON)
        print("Increase mat duty cycle")
    elif temp > MAT_TEMP_UPPER_BOUND:
        # decrease mat duty cycle
        set_mat(OFF)
        print("Decrease mat duty cycle")
    else:
        print("No change to mat duty cycle")
        # no change

def get_dht_data(dht_sensor):
    line_number = dht_sensor.number + 2
    sensor_number_string = str(dht_sensor.number)

    if dht_sensor.disabled:
        display.lcd_display_string(dht_sensor.disabled_string, line_number)
        return None, None

    try: 
        hum, temp = dht_sensor.get_data_f()

    except RuntimeError as error:
        # TODO: Handle error - ALARM
        #display.lcd_display_string("Check sensor " + sensor_number_string + " conn!", line_number)
        print("Exception while polling sensor " + sensor_number_string + ": " + str(error))
        return None, None

    if (temp > 50 and temp <= 120) and (hum > 0 and hum <= 100):
        display.lcd_display_string("{0}: T:{1:0.2f}F H:{2:0.2f}%".format(sensor_number_string, temp, hum), line_number)
        return hum, temp
    else:
        print("Bad sensor data")
        return None, None

def run_dht(dhts):
    # Support for multiple DHTs
    temp = 0
    hum = 0
    sensors = len(dhts)
    
    for dht in dhts:
        dht_hum, dht_temp = get_dht_data(dht)
        if dht_temp and dht_hum:
            # Only add if sensor returns good data
            temp += dht_temp
            hum += dht_hum
        else:
            sensors -= 1
    
    if sensors < 1:
        # not enough sensors to continue operation
        # TODO: kill relay?
        print("Not enough sensors to calculate duty cycle!")
        return
    
    avg_temp = temp/sensors
    avg_hum = hum/sensors

    if avg_hum < HUMIDITY_LOWER_BOUND:
        set_fogger(ON)
    elif avg_hum > HUMIDITY_UPPER_BOUND:
        set_fogger(OFF)
    else:
        print("Humidity good")

    if avg_temp < AMBIENT_TEMP_LOWER_BOUND:
        set_light(ON)
    elif avg_temp > AMBIENT_TEMP_UPPER_BOUND:
        set_light(OFF)
    else:
        print("Ambient temp good")

def poll_sensor_loop():
    while True:
        try:
            run_probe([probe])
            sleep(.1)
            run_dht([dht1, dht2])
            sleep(.1)
        except KeyboardInterrupt:
            print("Stopping...")
            GPIO.cleanup()
            display.lcd_clear()
            display.backlight(OFF)
            break

if __name__ == "__main__":
    process = Process(target=poll_sensor_loop)
    process.start()
    app.run(host='0.0.0.0', port=80, use_reloader=False)
    process.join()
