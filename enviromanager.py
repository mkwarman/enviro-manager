import time
from core import core

CONFIG_FILE = '.env'
SENSORS_FILE = 'sensors.json'

def poll(sources):
    print(sources.poll())

def start_loop(config, sources):
    start_time = time.time()
    loop_time = config.getfloat('PollFrequency')
    try:
        while True:
            poll(sources)
            time.sleep(loop_time - ((time.time() - start_time) % loop_time))
    except KeyboardInterrupt:
        return

if __name__ == "__main__":
    config = core.load_config(CONFIG_FILE)
    sources = core.get_sources(SENSORS_FILE)
    start_loop(config, sources)
