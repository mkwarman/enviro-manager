from random import randint

from datasource.types.randomdata import RandomData
from ..datasource import DataSource

KEY = 'RandomData2'

class RandomData2(DataSource):
    def __init__(self, options):
        super().__init__(options['name'])

    def has_data(self):
        return True

    def get_data(self):
        return randint(100, 200)

def get_class(options):
    return RandomData2(options)