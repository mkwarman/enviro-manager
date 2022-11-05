import time
from random import randint
from ..datasource import DataSource

KEY = 'RandomData'


class RandomData(DataSource):
    def __init__(self, options):
        super().__init__(options['name'])
        self.rand_min = int(options['rand_min'])
        self.rand_max = int(options['rand_max'])
        self.sampling_rate = float(options['sampling_rate'])
        self.last_read_time = 0.0

    def has_data(self):
        return (time.time() - self.last_read_time) > self.sampling_rate

    def get_data(self):
        self.last = randint(self.rand_min, self.rand_max)
        self.last_read_time = time.time()
        return self.last

    def get_last(self):
        return self.last


def get_instance(options):
    return RandomData(options)
