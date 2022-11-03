import time
import configparser
import json
from datasource.datasources import DataSources

CONFIG_FILE = '.env'
SENSORS_FILE = 'sensors.json'

def load_config():
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    environment = config['DEFAULT']['Environment']
    return config[environment]

def get_sources(config = {}):
    sources = DataSources()

    with open(SENSORS_FILE, 'r') as f:
        for source_definition in json.loads(f.read()):
            sources.add_from_definition(source_definition)

    return sources

def poll(sources):
    print(sources.poll())

def start_loop(config, sources):
    start_time = time.time()
    loop_time = config.getfloat('PollFrequency')
    while True:
        poll(sources)
        time.sleep(loop_time - ((time.time() - start_time) % loop_time))

if __name__ == "__main__":
    config = load_config()
    sources = get_sources(config)
    start_loop(config, sources)
