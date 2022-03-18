import numpy as np
from typing import List

class Bounds:
    def __init__(self, dims: int):
        if not 1 <= dims <= 3:
            raise ValueError(f"Bounds dimension must be between 1 and 3, but received: {dims}")
        self.dims = dims
        # 1D data has form: [[t_min, t_max], [x_min, x_max]]
        # 2D data has form: [[t_min, t_max], [x_min, x_max], [y_min, y_max]]
        # 3D data has form: [[t_min, t_max], [x_min, x_max], [y_min, y_max], [z_min, z_max]]
        self.values = np.zeros([2, dims + 1])

    @property
    def t(self) -> np.ndarray.view:
        return self.values[:, 0]
    
    @t.setter
    def t(self, value: List) -> None:
        self.values[:, 0] = value
    
    @property
    def x(self) -> np.ndarray.view:
        return self.values[:, 1]
    
    @property
    def y(self) -> np.ndarray.view:
        return self.values[:, 2]
    
    @property
    def z(self) -> np.ndarray.view:
        return self.values[:, 3]
    
    def update(self, data: np.array) -> None:
        pass