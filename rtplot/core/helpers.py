import numpy as np


def require_keys(keys, d):
    for key in keys:
        if key not in d:
            raise Exception(f"Missing required keyword argument {key}.")


def circle(**kwargs):
    require_keys(["xy", "radius"], kwargs)
    params = {}
    params.update(**kwargs)
    return {"circle": params}


def point(**kwargs):
    require_keys(["xy"], kwargs)
    params = {}
    params.update(**kwargs)
    return {"point": params}


def vline(**kwargs):
    require_keys(["x"], kwargs)
    params = {}
    params.update(**kwargs)
    return {"vline": params}


def hline(**kwargs):
    require_keys(["y"], kwargs)
    params = {}
    params.update(**kwargs)
    return {"hline": params}


def rectangle(**kwargs):
    require_keys(["xy", "width", "height"], kwargs)
    params = {}
    params.update(**kwargs)
    return {"rectangle": params}


def get_data_characteristics(array):
    num_coords = None
    num_lines = None

    try:
        num_coords = np.size(array, 1)
        num_lines = np.size(array, 0)
    except IndexError:
        num_coords = np.size(array)
        num_lines = 1

    return (num_coords, num_lines)
