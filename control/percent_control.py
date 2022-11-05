from abc import abstractmethod
from .control import Control


class PercentControl(Control):
    @property
    def current_percent(self):
        return self._current_percent

    def set_percent(self, percent):
        self._current_percent = percent
        self.handle_set_percent()

    """
    PercentControls must implement handle_set_percent that accepts a numeric
    value corresponding to the percent output that the control should be set to
    """
    @abstractmethod
    def handle_set_percent(self, percent):
        pass
