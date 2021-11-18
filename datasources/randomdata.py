from random import randint
from .datasource import DataSource

class RandomData(DataSource):
    def __init__(self, name):
        super().__init__(name)

    def has_data(self):
        return True

    def get_data(self):
        return randint(1, 10)
