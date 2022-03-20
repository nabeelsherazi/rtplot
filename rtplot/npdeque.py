import numpy as np

class DequeArray:
    """
    Dynamically resizing deque implemented over a numpy array.
    Fixed num_cols, and num_slices, expanding num_rows.
    """

    MAX_NUM_ROWS = 2**16

    def __init__(self, num_data_dims: int, num_data_series: int, initial_num_rows: int = 1024):
        # Number of columns in Y is fixed
        self.num_cols_y: int = num_data_dims

        # Number of columns in Z is fixed
        self.num_cols_z: int = num_data_series
        
        # Data stored here
        self.data = np.zeros((initial_num_rows, num_data_dims, num_data_series))

        # Current start and end indices
        self.start: int = 0
        self.end: int = 0

    @property
    def capacity(self) -> int:
        return self.data.shape[0]

    def size(self) -> int:
        return self.end - self.start
    
    def empty(self) -> bool:
        return self.end == self.start

    def resize_if_needed(self) -> None:
        if (self.end + 1) % self.capacity >= self.start:
            # Do resize
            new_data = np.zeros((self.capacity * 2, self.num_cols_y, self.num_cols_z))
            start_to_wrap = self.capacity - self.start
            new_data[0:start_to_wrap, :, :] = self.data[self.start:, :, :]
            end_to_start = self.end


    def clear(self) -> None:
        self.start = 0
        self.end = 0
    
    def append(self, slice: np.ndarray) -> None:
        self.resize_if_needed()
        self.data[self.end, :, :] = slice[:, :]
        self.end = (self.end + 1) % self.capacity

    def pop(self) -> np.ndarray:
        if not self.empty():
            slice = self.data[self.start, :, :]
            self.start = (self.start + 1) % self.capacity
            return slice
        else:
            raise IndexError("Deque is empty")
    
    def popleft(self) -> np.ndarray:
        if not self.empty():
            slice = self.data[self.end, :, :]
            self.end = (self.end - 1) % self.capacity
            return slice
        else:
            raise IndexError("Deque is empty")