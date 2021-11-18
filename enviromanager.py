import time
import configparser
import json
from datasource.datasources import DataSources

CONFIG_FILE = '.env'

def load_config():
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    environment = config['DEFAULT']['Environment']
    return config[environment]

def get_sources(config):
    sources = DataSources()
    source_definitions = config.get('DataSources')
    for source_definition in json.loads(source_definitions):
        sources.add_from_definition(source_definition)
    return sources

def poll(sources):
    print('polling...')
    sources.print()

def start_loop(config, sources):
    start_time = time.time()
    loop_time = config.getfloat('PollFrequency')
    print("Loop time:", loop_time)
    while True:
        poll(sources)
        time.sleep(loop_time - ((time.time() - start_time) % loop_time))

if __name__ == "__main__":
    config = load_config()
    sources = get_sources(config)
    start_loop(config, sources)
