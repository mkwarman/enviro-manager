from abc import ABC
from .datasource import DataSource

class DataSources(ABC):
    def __init__(self):
        self.data_sources = []
    
    def add(self, datasource: DataSource):
        self.data_sources.append(datasource)

    def print(self):
        [data_source.print() for data_source in self.data_sources]