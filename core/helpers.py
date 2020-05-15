import numpy as np

def require_keys(keys, d):
    for key in keys:
        if key not in d:
            raise Exception(f"Missing required keyword argument {key}.")

def circle(**kwargs):
    require_keys(["xy", "radius"], kwargs)
    params = {}
    params.update(**kwargs)
    return {"circle" : params}

def point(**kwargs):
    require_keys(["xy"], kwargs)
    params = {}
    params.update(**kwargs)
    return {"point" : params}

def vline(**kwargs):
    require_keys(["x"], kwargs)
    params = {}
    params.update(**kwargs)
    return {"vline" : params}

def hline(**kwargs):
    require_keys(["y"], kwargs)
    params = {}
    params.update(**kwargs)
    return {"hline" : params}

def rectangle(**kwargs):
    require_keys(["xy", "width", "height"], kwargs)
    params = {}
    params.update(**kwargs)
    return {"rectangle" : params}
