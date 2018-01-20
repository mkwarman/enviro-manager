def get_probe_data(probe):
    if probe.disabled:
        return None, probe.disabled_string

    try:
        temp = probe.get_temp_f()

    except (RuntimeError, IOError) as error:
        # TODO: Handle error - ALARM
        print("Exception while polling probe: " + str(error))
        return None, "Check probe conn!"

    return temp, "Probe Temp: {0:0.2f}F".format(temp)

def get_dht_data(dht_sensor):
    if dht_sensor.disabled:
        return None, None, dht_sensor.disabled_string

    try:
        hum, temp = dht_sensor.get_data_f()

    except RuntimeError as error:
        # TODO: Handle error - ALARM
        #display.lcd_display_string("Check sensor " + str(dht_sensor.number) + " conn!", line_number)
        print("Exception while polling sensor " + str(dht_sensor.number) + ": " + str(error))
        return None, None, None

    if (temp > 50 and temp <= 120) and (hum > 0 and hum <= 100):
        return hum, temp, "{0}: T:{1:0.2f}F H:{2:0.2f}%".format(dht_sensor.number, temp, hum)
    else:
        print("Bad sensor data")
        return None, None, None
