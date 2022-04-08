import time
import numpy as np
from enum import Enum, unique
import random


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

def s2ns(secs: float) -> float:
    return secs * 1E9

def ns2s(nsecs: float) -> float:
    return nsecs / 1E9