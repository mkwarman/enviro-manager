# Imports
import time
import configparser
from datasources.randomdata import RandomData
from datasources.datasources import DataSources

CONFIG_FILE = '.env'

def load_config():
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    environment = config['DEFAULT']['Environment']
    return config[environment]

def get_sources():
    sources = DataSources()
    for x in range(5):
        sources.add(RandomData(str(x)))
    return sources

def run(sources):
    print('polling...')
    sources.print()

def start_loop(config, sources):
    start_time = time.time()
    loop_time = config.getfloat('PollFrequency')
    print("Loop time:", loop_time)
    while True:
        run(sources)
        time.sleep(loop_time - ((time.time() - start_time) % loop_time))

if __name__ == "__main__":
    config = load_config()
    sources = get_sources()
    start_loop(config, sources)