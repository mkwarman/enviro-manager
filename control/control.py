from abc import ABC, abstractmethod


class Control(ABC):
    def __init__(self, name):
        self.name = name

    @property
    def is_on(self):
        return self._is_on

    def set_on(self, value):
        self._is_on = value
        self.handle_set_on()

    """
    Controls must implement handle_set_on that accepts a boolean True or False
    indicating whether the control should be on or off, respectively
    """
    @abstractmethod
    def handle_set_on(self, value):
        pass
