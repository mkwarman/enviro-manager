import re

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
