import json
import configparser
from datasource.datasources import DataSources

def load_config(config_file):
    config = configparser.ConfigParser()
    config.read(config_file)
    environment = config['DEFAULT']['Environment']
    return config[environment]

def get_sources(sensors_file):
    sources = DataSources()

    with open(sensors_file, 'r') as f:
        for source_definition in json.loads(f.read()):
            sources.add_from_definition(source_definition)

    return sources