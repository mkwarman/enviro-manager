from random import randint
from ..datasource import DataSource

KEY = 'RandomData'

class RandomData(DataSource):
    def __init__(self, options):
        super().__init__(options['name'])

    def has_data(self):
        return True

    def get_data(self):
        return randint(1, 10)

def get_class(options):
    return RandomData(options)
