import re
import Adafruit_DHT

DHT22_RETRIES = 3
TRIES_BEFORE_DISABLE = 3
REGEX = re.compile(r'YES\n[\w ]*t=(\d+)$')

# DS18b20
class Probe:
    concurrent_failures = 0
    disabled = False
    disabled_string = "Probe disabled"

    def __init__(self, path):
        self.path = path

    def get_temp_c(self):
        try:
            probe_file = open(self.path)
            regex_result = REGEX.search(probe_file.read())
            if self.concurrent_failures != 0:
                self.concurrent_failures = 0
        except Exception as e:
            self.increment_read_failures()
            raise IOError('Could not open probe data file: ' + str(e))

        if regex_result:
            temp_string = regex_result.group(1)
            #temp_c =
            return (int(temp_string)/1000)
            #return round((temp_c if c_or_f == "c" else to_f(temp_c)), 3)
        else:
            print("Probe regex could not find temp")
            self.increment_read_failures()
            raise RuntimeError('Probe regex could not find temp')

    def get_temp_f(self):
        return (self.get_temp_c() * 1.8) + 32
    
    def increment_read_failures(self):
        self.concurrent_failures += 1
        if self.concurrent_failures >= TRIES_BEFORE_DISABLE:
            self.disabled = True
            self.disabled_string = ("Check probe conn!")



# DHT22
class DHT22:
    sensor = Adafruit_DHT.DHT22
    concurrent_failures = 0
    disabled = False

    def __init__(self, pin, number):
        self.pin = pin
        self.number = number
        self.disabled_string = "Sensor " + str(number) + " disabled"

    def get_data_c(self):
        humidity, temperature_c = Adafruit_DHT.read_retry(self.sensor, self.pin, DHT22_RETRIES)
        if not (isinstance(humidity, float) and isinstance(temperature_c, float)):
            self.increment_read_failures()
            raise RuntimeError('Sensor poll failed')
        elif self.concurrent_failures != 0:
            print("resetting failures")
            self.concurrent_failures = 0

        return humidity, temperature_c

    def get_data_f(self):
        humidity, temperature_c = self.get_data_c()
        temperature_f = (temperature_c * 1.8) + 32
        return humidity, temperature_f

    def increment_read_failures(self):
        self.concurrent_failures += 1
        print("incrementing failures, now: " + str(self.concurrent_failures))
        if self.concurrent_failures >= TRIES_BEFORE_DISABLE:
            self.disabled = True
            self.disabled_string = ("Check sensor " + str(self.number) + " conn!")
