from abc import ABC, abstractmethod

class Shape(ABC):
    @abstractmethod
    def __init__(self):
        pass
    @abstractmethod
    def to_vrml(self):
        pass