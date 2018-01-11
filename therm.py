import re

PROBE = "28-0317030193ff"
DIRECTORY = "/sys/bus/w1/devices/"
FILE = DIRECTORY + PROBE + "/w1_slave"

REGEX = re.compile(r'YES\n[\w ]*t=(\d+)$')

def get_temp(c_or_f):
    file = open(FILE)
    regex_result = REGEX.search(file.read())
    if regex_result:
        temp_string = regex_result.group(1)
        temp_c = int(temp_string)/1000
        return round((temp_c if c_or_f == "c" else to_f(temp_c)), 3)
    else:
        print("No temp")

def to_f(temp_c):
    return (temp_c * 1.8) + 32
