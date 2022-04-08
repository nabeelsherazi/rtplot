import numpy as np

class DequeArray:
    """
    Dynamically resizing deque implemented over a numpy array.
    Fixed num_cols, and num_slices, expanding num_rows.
    """

    MAX_NUM_ROWS = 2**16

    def __init__(self, num_data_dims: int, num_data_series: int, initial_num_rows: int = 8):
        # Number of columns in Y is fixed
        self.num_cols_y: int = num_data_dims

        # Number of columns in Z is fixed
        self.num_cols_z: int = num_data_series
        
        # Data stored here
        self.data = np.zeros((initial_num_rows, num_data_dims, num_data_series))

        # Current start and end indices
        # Start will always represent the index to be popped next
        self.start: int = 0
        # End will always represent the index to assign to next
        self.end: int = 0

        # Counter of number of elements
        self.count: int = 0

    def __index__(self, key: slice) -> np.ndarray:
        return self.data[key]

    def log(self) -> None:
        print(f"start: {self.start}, end: {self.end}, count: {self.count}, capacity: {self.capacity()}")

    def capacity(self) -> int:
        return self.data.shape[0]

    def size(self) -> int:
        if self.end > self.start:
            self.log()
            assert self.count == self.end - self.start
        elif self.end < self.start:
            self.log()
            assert self.count == self.capacity() - self.start + self.end
        elif self.end == self.start:
            self.log()
            assert self.count == 0
        return self.count
    
    def empty(self) -> bool:
        # Debug only checks
        if self.count == 0:
            assert self.end == self.start
        return self.count == 0
    
    def full(self) -> bool:
        # Debug only checks
        if self.count + 1 == self.capacity():
            self.log()
            assert (self.end + 1) % self.capacity() == self.start
        return (self.end + 1) % self.capacity() == self.start

    def resize(self) -> None:
        "Double size"
        if (self.capacity() * 2 > self.MAX_NUM_ROWS):
            raise MaxSizeExceededError(f"Deque size {self.size()} required resize that would exceed MAX_NUM_ROWS: {self.MAX_NUM_ROWS}")
        new_data = np.zeros((self.capacity() * 2, self.num_cols_y, self.num_cols_z))
        if self.end >= self.start:
            new_data[0:self.size(), :, :] = np.copy(self.data[self.start:self.end, :, :])
        else:
            # Start to wrap
            first_run_length: int = self.capacity() - self.start
            new_data[0:first_run_length, :, :] = np.copy(self.data[self.start:, :, :])
            # Wrap to end
            second_run_length: int = self.end
            new_data[first_run_length:(first_run_length + second_run_length), :, :] = np.copy(self.data[0:self.end, :, :])
        # New is old
        self.data = new_data


    def clear(self) -> None:
        self.start = 0
        self.end = 0
        self.count = 0
    
    def append(self, s: np.ndarray) -> None:
        if self.full():
            self.resize()
        self.data[self.end, :, :] = np.copy(s[:, :])
        self.end = (self.end + 1) % self.capacity()
        self.count += 1

    def pop(self) -> np.ndarray:
        if not self.empty():
            s = self.data[self.start, :, :]
            self.start = (self.start + 1) % self.capacity()
            self.count -= 1
            return s
        else:
            raise IndexError("Deque is empty")
    
    def popleft(self) -> np.ndarray:
        if not self.empty():
            s = self.data[self.end, :, :]
            self.end = (self.end - 1) % self.capacity()
            self.count -= 1
            return s
        else:
            raise IndexError("Deque is empty")

class MaxSizeExceededError(Exception):
    """Raised if deque size exceeds MAX_NUM_ROWS"""
    pass