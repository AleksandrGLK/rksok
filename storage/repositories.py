from typing import NamedTuple
from abc import ABC, abstractmethod

from resources import strings


class DataStorageInterface(ABC):
    """Simple data storage interface."""

    @abstractmethod
    def get_data(self, message: NamedTuple):
        pass

    @abstractmethod
    def delete_data(self, message: NamedTuple):
        pass

    @abstractmethod
    def post_data(self, message: NamedTuple):
        pass



