import Adafruit_DHT
import datetime

DHT22_RETRIES = 10
TRIES_BEFORE_DISABLE = 10

# DHT22
class DHT22:
    sensor = Adafruit_DHT.DHT22
    concurrent_failures = 0
    total_failures = 0
    disabled = False
    last_updated = None
    name = ""

    def __init__(self, pin, number, name):
        self.pin = pin
        self.number = number
        self.disabled_string = "Sensor " + str(number) + " disabled"
        self.name = name

    def get_data_c(self):
        humidity, temperature_c = Adafruit_DHT.read_retry(self.sensor, self.pin, DHT22_RETRIES)
        if not (isinstance(humidity, float) and isinstance(temperature_c, float)):
            self.increment_read_failures()
            raise RuntimeError('Sensor poll failed')
        else:
            self.last_updated = datetime.datetime.now();
            if self.concurrent_failures != 0:
                print("resetting failures")
                self.concurrent_failures = 0

        return humidity, temperature_c

    def get_data_f(self):
        humidity, temperature_c = self.get_data_c()
        temperature_f = (temperature_c * 1.8) + 32
        return humidity, temperature_f

    def increment_read_failures(self):
        self.concurrent_failures += 1
        self.total_failures += 1
        print("incrementing failures, now: " + str(self.concurrent_failures))
        if self.concurrent_failures >= TRIES_BEFORE_DISABLE:
            self.disabled = True
            self.disabled_string = ("Check sensor " + str(self.number) + " conn!")
