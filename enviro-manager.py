from probe import Probe
from dht22 import DHT22
from time import sleep
from flask import Flask, Markup, render_template
from flask_socketio import SocketIO, emit
from duty_cycle import DutyCycle
from display import Display
import argparse
import pickle
import datetime
import gpio
import sys
import sensor
import serial
import requests
import os
import eventlet
import settings

eventlet.monkey_patch()

app = Flask(__name__)
# Set up encryption
app.config['DEBUG'] = False

socketio = SocketIO(app)
config = settings.Config()

MAT_SERIAL_IDENTIFIER = "M"
LIGHT_SERIAL_IDENTIFIER = "L"
ZERO_CROSS_IDENTIFIER = "Z"

ON = 1
OFF = 0

MAT_TEMPERATURE_APPROACH_DELTA_LIMIT = 0.12
AMBIENT_TEMPERATURE_APPROACH_DELTA_LIMIT = 0.2

display = Display()
probe = Probe(config.get('probe', 'READ_DIRECTORY'), 'Probe')
dht1_temp = DHT22(gpio.DHT_SENSOR1_PIN, 1, 'Sensor1 (temperature)')
dht2_humidity = DHT22(gpio.DHT_SENSOR2_PIN, 2, 'Sensor2 (humidity)')
mat = DutyCycle("Mat", MAT_SERIAL_IDENTIFIER)
light = DutyCycle("Light", LIGHT_SERIAL_IDENTIFIER)

light.duty_cycle_delta = 10

serialConnection = serial.Serial('/dev/serial0', 9600)

poll_sensors = True

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

parser = argparse.ArgumentParser()
parser.add_argument('--gpio_disabled', action="store_true")
parser.add_argument('--load_file', action="store_true")
args = parser.parse_args()

if args.gpio_disabled:
    gpio.enabled(False)
if args.load_file:
    with open(config.get('save_file', 'NAME'), 'rb') as f:
        light = pickle.load(f)
        mat = pickle.load(f)
    print("Sending loaded values...")
    light.send_to_arduino(serialConnection)
    mat.send_to_arduino(serialConnection)

def send_alert(title, body):
    payload = '{"body": \"' + body + '\", "title": \"' + title + '\", "type": "note"}'
    headers = {'Access-Token': config.get('external', 'PUSHBULLET_TOKEN'), 'Content-Type': 'application/json'}
    url = config.get('external', 'PUSHBULLET_URL')
    print("Attempting to send alert with title: \"" + title + "\" and body:\n" + body)
    r = requests.post(url, data=payload, headers=headers)
    print("response: " + r.text)
    return r

def run_probe(probe):
    """
    # Support for multiple probes
    temp = 0

    for probe in probes:
        temp += probe.get_probe_data(probe)

    avg_temp = temp/len(probes)
    """
    temp, display_string = sensor.get_probe_data(probe)
    display.update(display_string, 2)

    if not temp:
        if probe.concurrent_failures == config.getint('alert', 'CONCURRENT_READ_FAILURE_ALERT_THRESHOLD'):
            gpio.set_mat(OFF)
            send_alert("Read Error", str(probe.concurrent_failures) + " probe read failures in a row")

        # no useable data
        print("Not enough data to calculate duty cycle!")
        return
    elif probe.concurrent_failures != 0:
        probe.concurrent_failures = 0

    global probe_temp
    previous_temp = probe_temp
    probe_temp = temp

    section = 'mat_bounds'
    lower_bound = config.getint(section, 'LOWER')
    target      = config.getint(section, 'TARGET')
    upper_bound = config.getint(section, 'UPPER')
    danger_zone = config.getint(section, 'DANGER_ZONE')

    if temp < target:
        gpio.set_mat(ON)
        if temp < lower_bound:
            print("Max mat duty cycle")
            mat.max_duty_cycle(serialConnection)
        elif (previous_temp > temp):
            print("Increase mat duty cycle")
            mat.increase_duty_cycle(serialConnection)
        elif (temp - previous_temp > MAT_TEMPERATURE_APPROACH_DELTA_LIMIT):
            print("Decrease mat duty cycle due to approach speed")
            mat.decrease_duty_cycle(serialConnection)
    elif temp > target:
        if temp > upper_bound:
            gpio.set_mat(OFF)
            if temp > danger_zone:
                send_alert("Temperature Alert", "Mat temperature too high: " + str(temp))
        # Dont mess with duty cycle if state is off
        elif (gpio.mat_state == ON):
            if (previous_temp < temp):
                print("Decrease mat duty cycle")
                mat.decrease_duty_cycle(serialConnection)
            elif (previous_temp - temp > MAT_TEMPERATURE_APPROACH_DELTA_LIMIT):
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
        if dht.concurrent_failures == config.getint('alert', 'CONCURRENT_READ_FAILURE_ALERT_THRESHOLD'):
            gpio.set_light(OFF)
            send_alert("Read Error", str(dht.concurrent_failures) + " temp DHT read failures in a row")
        print("DHT temp sensor didn't return usable data")
        return

    if display_string:
        display.update(display_string, dht.number + 2)

    global ambient_temp
    previous_ambient_temp = ambient_temp
    ambient_temp = dht_temp

    section = 'ambient_bounds'
    lower_bound = config.getint(section, 'LOWER')
    target      = config.getint(section, 'TARGET')
    upper_bound = config.getint(section, 'UPPER')
    danger_zone = config.getint(section, 'DANGER_ZONE')
    
    if ambient_temp < target:
        gpio.set_light(ON)
        if ambient_temp < lower_bound:
            print("Max light duty cycle")
            light.max_duty_cycle(serialConnection)
        # If temperature falling
        elif (previous_ambient_temp > ambient_temp):
            print("Increase light duty cycle")
            light.increase_duty_cycle(serialConnection)
        elif (ambient_temp - previous_ambient_temp > AMBIENT_TEMPERATURE_APPROACH_DELTA_LIMIT):
            print("Decrease light duty cycle due to approach speed")
            light.decrease_duty_cycle(serialConnection)
    elif ambient_temp > target:
        if ambient_temp > upper_bound:
            gpio.set_light(OFF)
            if ambient_temp > danger_zone:
                send_alert("Temperature Alert", "Ambient temperature too high: " + str(ambient_temp))
        # Dont mess with duty cycle if state is off
        elif (gpio.light_state == ON):
            if (previous_ambient_temp < ambient_temp):
                print("Decrease light duty cycle")
                light.decrease_duty_cycle(serialConnection)
            elif (previous_ambient_temp - ambient_temp > AMBIENT_TEMPERATURE_APPROACH_DELTA_LIMIT):
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
        display.update(display_string, dht.number + 2)

    section = 'humidity_bounds'
    lower_bound = config.getint(section, 'LOWER')
    upper_bound = config.getint(section, 'UPPER')

    if dht_hum < lower_bound:
        gpio.set_fogger(ON)
        print("Turn on fogger")
    elif dht_hum > upper_bound:
        print("Turn off fogger")
        gpio.set_fogger(OFF)

def poll_sensor_loop():
    while poll_sensors:
        try:
            if (config.getboolean('application_status', 'MAT')):
                run_probe(probe)
                socketio.emit('sensor_update',
                    {'sensors': get_sensors_object(), 'appliances': get_appliances_object()},
                    namespace='/live')
            eventlet.sleep(1)
            if (config.getboolean('application_status', 'LIGHT')):
                run_dht_temp(dht1_temp)
                socketio.emit('sensor_update',
                    {'sensors': get_sensors_object(), 'appliances': get_appliances_object()},
                    namespace='/live')
            eventlet.sleep(1)
            if (config.getboolean('application_status', 'FOGGER')):
                run_dht_humidity(dht2_humidity)
                socketio.emit('sensor_update',
                    {'sensors': get_sensors_object(), 'appliances': get_appliances_object()},
                    namespace='/live')
            eventlet.sleep(1)
        except (KeyboardInterrupt, SystemExit) as exit:
            # if we catch stop signal here instead of in the parent process
            print("Stopping background process...")
            gpio.cleanup()
            display.off()
            print("Stopping server")
            socketio.stop()
            return False

        except Exception as error:
            send_alert("Exception occurred", "Uncaught exception occurred. Stack trace to follow (hopefully)")
            send_alert("Exception:", str(error))
            pass

    gpio.cleanup()
    display.off()

def get_sensors_object():
    now = datetime.datetime.now()
    # Full Date format: "({1:%H:%M:%S %Y-%m-%d})" 
    # Dont forget to add [sensor].last_updated to .format(...) section (note the "1:" above)
    probe_last_updated = "{0}s ago" \
            .format((now - probe.last_updated).seconds) if probe.last_updated else "never"
    dht1_temp_last_updated = "{0}s ago" \
            .format((now - dht1_temp.last_updated).seconds) if dht1_temp.last_updated else "never"
    dht2_humidity_last_updated = "{0}s ago" \
            .format((now - dht2_humidity.last_updated).seconds) if dht2_humidity.last_updated else "never"
    mat_target      = config.getint('mat_bounds', 'TARGET')
    ambient_target  = config.getint('ambient_bounds', 'TARGET')
    hum_lower       = config.getint('humidity_bounds', 'LOWER')
    hum_upper       = config.getint('humidity_bounds', 'UPPER')
    sensors = [
        {
            'name': probe.name,
            'temperature': '{0:0.2f}F'.format(probe_temp),
            'target_temperature': "{0}F".format(mat_target),
            'humidity': Markup('<span class="na">N/A</span>'),
            'target_humidity': Markup('<span class="na">N/A</span>'),
            'last_updated': probe_last_updated,
            'concurrent_failures': probe.concurrent_failures,
            'total_failures': probe.total_failures
        },
        {
            'name': dht1_temp.name,
            'temperature': '{0:0.2f}F'.format(sensor_values[0].get('temp')),
            'target_temperature': "{0}F".format(ambient_target),
            'humidity': '{0:0.2f}%'.format(sensor_values[0].get('hum')),
            'target_humidity': Markup('<span class="na">N/A</span>'),
            'last_updated': dht1_temp_last_updated,
            'concurrent_failures': dht1_temp.concurrent_failures,
            'total_failures': dht1_temp.total_failures
        },
        {
            'name': dht2_humidity.name,
            'temperature': '{0:0.2f}F'.format(sensor_values[1].get('temp')),
            'target_temperature': Markup('<span class="na">N/A</span>'),
            'humidity': '{0:0.2f}%'.format(sensor_values[1].get('hum')),
            'target_humidity': '{0}% to {1}%'.format(hum_lower, hum_upper),
            'last_updated': dht2_humidity_last_updated,
            'concurrent_failures': dht2_humidity.concurrent_failures,
            'total_failures': dht2_humidity.total_failures
        }
    ]
    return sensors

def get_appliances_object():
    appliances = [
        {
            'name': mat.name,
            'enabled': config.getboolean('application_status', 'MAT'),
            'status': ("On" if gpio.mat_state == ON else "Off"),
            'duty_cycle': str(mat.duty_cycle),
            'duty_cycle_percentage': '{0:0.2f}%'.format(mat.get_duty_cycle_percentage())
        },
        {
            'name': light.name,
            'enabled': config.getboolean('application_status', 'LIGHT'),
            'status': ("On" if gpio.light_state == ON else "Off"),
            'duty_cycle': str(light.duty_cycle),
            'duty_cycle_percentage': '{0:0.2f}%'.format(light.get_duty_cycle_percentage())
        },
        {
            'name': 'Fogger',
            'enabled': config.getboolean('application_status', 'FOGGER'),
            'status': ("On" if gpio.fogger_state == ON else "Off"),
            'duty_cycle': Markup('<span class="na">N/A</span>'),
            'duty_cycle_percentage': Markup('<span class="na">N/A</span>')
        }
    ]
    return appliances

def save_state():
    global light
    global mat
    with open(config.get('save_file', 'NAME'), 'wb') as f:
        pickle.dump(light, f)
        pickle.dump(mat, f)

@socketio.on('connect', namespace='/live')
def live_connect():
    print('Client connected')

@socketio.on('disconnect', namespace='/live')
def live_disconnect():
    print('Client disconnected')

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html', sensors=get_sensors_object(), appliances=get_appliances_object())

@app.route('/old')
def old():
    now = datetime.datetime.now()
    probe_last_updated = "{0:%H:%M:%S %Y-%m-%d} --- {1} seconds ago" \
            .format(probe.last_updated, (now - probe.last_updated).seconds) if probe.last_updated else "never"
    dht1_temp_last_updated = "{0:%H:%M:%S %Y-%m-%d} --- {1} seconds ago" \
            .format(dht1_temp.last_updated, (now - dht1_temp.last_updated).seconds) if dht1_temp.last_updated else "never"
    dht2_humidity_last_updated = "{0:%H:%M:%S %Y-%m-%d} --- {1} seconds ago" \
            .format(dht2_humidity.last_updated, (now - dht2_humidity.last_updated).seconds) if dht2_humidity.last_updated else "never"
    mat_target      = config.getint('mat_bounds', 'TARGET')
    ambient_target  = config.getint('ambient_bounds', 'TARGET')
    hum_lower       = config.getint('humidity_bounds', 'LOWER')
    hum_upper       = config.getint('humidity_bounds', 'UPPER')
    return "<p><h1>Sensor Status:</h1>" \
            + "<h2>Probe temp: {0:0.2f} (target: {1}F)</br>".format(probe_temp, mat_target) \
            + "    Last updated: {0}</br>".format(probe_last_updated) \
            + (("<strong>" + probe.disabled_string + "</strong>") if probe.disabled else "") \
            + "Sensor1 (temperature): temp={0:0.2f}F hum={1:0.2f}% (target temperature: {2}F)</br>" \
              .format(sensor_values[0].get('temp'), sensor_values[0].get('hum'), ambient_target) \
            + "    Last updated: {0}</br>".format(dht1_temp_last_updated) \
            + (("<strong>" + dht1_temp.disabled_string + "</strong>") if dht1_temp.disabled else "") \
            + "Sensor2 (humidity): temp={0:0.2f}F hum={1:0.2f}% (target humidity range: {2}% to {3}%)</br>" \
              .format(sensor_values[1].get('temp'), sensor_values[1].get('hum'), hum_lower, hum_upper) \
            + "    Last updated: {0}</br>".format(dht2_humidity_last_updated) \
            + (("<strong>" + dht2_humidity.disabled_string + "</strong>") if dht2_humidity.disabled else "") \
            + "</h2></p>" \
            + "<p><h1>Appliance Status:</h1>" \
            + "<h2>Mat enabled: {0} --- Current status: {1} --- Duty Cycle: {2} (about {3:0.2f}%)</br>" \
              .format(config.getboolean('application_status', 'MAT'), ("on" if gpio.mat_state == ON else "off"), \
                      str(mat.duty_cycle), mat.get_duty_cycle_percentage()) \
            + "Light enabled: {0} --- Current status: {1} --- Duty Cycle: {2} (about {3:0.2f}%)</br>" \
              .format(config.getboolean('application_status', 'LIGHT'), ("on" if gpio.light_state == ON else "off"), \
                      str(light.duty_cycle), light.get_duty_cycle_percentage()) \
            + "Fogger enabled: {0} --- Current status: {1}</br>" \
              .format(config.getboolean('application_status', 'FOGGER'), ("on" if gpio.fogger_state == ON else "off")) \
            + "</h2></p>"

@app.route('/test_alert')
def test_alert():
    send_alert("Test Alert", "Test alert message requested")
    return "Ok"

@app.route('/test_exception')
def test_exception():
    raise Exception("Test exception requested")


@app.route('/status')
def status():
    return "Ok"

if __name__ == "__main__":
    try:
        process = eventlet.spawn(poll_sensor_loop)
        socketio.run(app, host='0.0.0.0', port=80, use_reloader=False)
    except (KeyboardInterrupt, SystemExit):
        pass
    
    except Exception as error:
        send_alert("Exception occurred", "Uncaught exception occurred. Stack trace to follow (hopefully)")
        send_alert("Exception:", str(error))
        gpio.cleanup()
        raise error

    if process:
        print("Stopping background process...")        
        poll_sensors = False
        process.wait()
    print("Saving state...")
    save_state()
    print("Done")
