from abc import ABC
from pkgutil import iter_modules
from importlib import import_module

from .datasource import DataSource
from . import types

def get_datasource_dict():
    datasource_dict = dict()
    prefix = types.__name__ + "."
    for importer, modname, ispkg in iter_modules(types.__path__, prefix):
        module = import_module(modname)
        datasource_dict[module.KEY] = module
    return datasource_dict

class DataSources(ABC):
    def __init__(self):
        self.datasources = []
        self.datasource_dict = get_datasource_dict()
    
    def add(self, datasource: DataSource):
        self.datasources.append(datasource)

    def add_from_definition(self, definition):
        if 'type' not in definition or 'options' not in definition:
            print("Malformed datasource definition")
        elif definition['type'] not in self.datasource_dict:
            print("Unknown datasource type: " + str(definition['type']))
        else:
            datasource_type = definition['type']
            datasource_options = definition['options']
            new_datasource = self.datasource_dict[datasource_type].get_class(datasource_options)
            self.add(new_datasource)

    def print(self):
        [data_source.print() for data_source in self.datasources]

    def get_datasource_dict(self):
        return self.datasource_dict