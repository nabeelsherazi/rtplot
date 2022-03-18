import time
import numpy as np
from enum import Enum, unique
import random


@unique
class RtplotEvent(Enum):
    REQUEST_KILL = 1
    INTERNAL_PLOT_ERROR = 2
    TIMED_OUT = 3
    USER_ERROR = 4
    LINES_MISMATCH = 5


def require_keys(keys, d):
    for key in keys:
        if key not in d:
            raise Exception(f"Missing required keyword argument {key}.")


def get_data_characteristics(array: np.array):
    num_coords = None
    num_lines = None

    try:
        num_coords = np.size(array, 1)
        num_lines = np.size(array, 0)
    except IndexError:
        num_coords = np.size(array)
        num_lines = 1

    return (num_coords, num_lines)


def random_walk(bounds=(10, 10)):
    """ Bounces around """
    rnd = random.Random()
    xbound = bounds[0]
    ybound = bounds[1]
    x = 0.00
    y = 0.00
    vx = 0.5 + rnd.random() / 2
    vy = 0.5 + rnd.random() / 2
    while True:
        if abs(x) >= xbound:
            vx = -vx
        if abs(y) >= ybound:
            vy = -vy

        if rnd.random() > 0.9:
            if rnd.random() >= 0.5:
                vx = np.sign(vx) * (0.5 + rnd.random() / 2)
            else:
                vy = np.sign(vy) * (0.5 + rnd.random() / 2)

        x += vx
        y += vy
        yield (x, y)


def random_timeseries():
    y = 5
    rnd = random.Random()

    while True:
        if rnd.random() > 0.5:
            y += 0.1 * rnd.random()
        else:
            y -= 0.1 * rnd.random()
        yield y


def sinusoid(A, omega):
    phi = 0.00
    while True:
        phi += 0.01
        yield A * float(np.sin(omega * phi))


class Timer:
    def __init__(self, for_secs):
        self.start_time = time.perf_counter()
        self.end_time = self.start_time + for_secs

    @property
    def done(self):
        return time.perf_counter() >= self.end_time


def min_and_max(data):
    """
    Return the min and max of a given numpy array, as a tuple
    """
    return (np.amin(data), np.amax(data))


def get_data_bounds(data_list):
    bounds = []
    for data in data_list:
        (dmin, dmax) = min_and_max(data)
        drange = dmax - dmin
        bounds.append({"range": drange, "min": dmin, "max": dmax})
    return bounds

def s2ns(secs):
    return secs * 1E9