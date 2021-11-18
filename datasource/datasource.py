from abc import ABC, abstractmethod

class DataSource(ABC):
    def __init__(self, name):
        self.name = name

    @abstractmethod
    def has_data(self):
        pass

    def print(self):
        print(self.name)