from abc import ABC, abstractmethod


class DataSource(ABC):
    def __init__(self, name):
        self.name = name

    """
    Datasources must implement has_data() that returns a boolean True or False
    indicating whether or not the datasource has data available.

    For example, the DHT22 sensor has a sampling rate of 0.5Hz, so its
    has_data() function should only return true after two seconds have elapsed
    since its last reading.
    """
    @abstractmethod
    def has_data(self):
        pass

    """
    Datasources must implement get_data() that returns the current value from
    the datasource.
    """
    @abstractmethod
    def get_data(self):
        pass

    """
    Datasources must implement get_last() that returns the last value read
    from the datasource. This will most often be used when has_data() returns
    False.
    """
    @abstractmethod
    def get_last(self):
        pass

    def get_name(self):
        return self.name

    def print(self):
        print(self.name)
