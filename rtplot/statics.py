from matplotlib import pyplot as plt
from dataclasses import dataclass
from abc import ABC

class Static(ABC):
    def generate(self):
        pass

@dataclass
class Circle(Static):
    x: int
    y: int
    radius: float
    params = {}

    def generate(self):
        return plt.Circle((self.x, self.y), self.width, self.height, **self.params)

@dataclass
class Rectangle(Static):
    x: int
    y: int
    width: int
    height: int
    params = {}

    def generate(self):
        return plt.Rectangle((self.x, self.y), self.width, self.height, **self.params)

@dataclass
class VLine(Static):
    x: int
    params = {}

    def generate(self):
        return plt.axvline(self.x, **self.params)


@dataclass
class HLine(Static):
    y: int
    params = {}
    def generate(self):
        return plt.axyline(self.y, **self.params)