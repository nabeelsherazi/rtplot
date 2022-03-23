import pytest
import numpy as np
from rtplot.npdeque import DequeArray

@pytest.fixture
def empty_deque():
    data = DequeArray(3, 3)
    return data

@pytest.fixture
def loaded_deque(empty_deque: DequeArray):
    for _ in range(100):
        empty_deque.append(np.random.rand(3, 3))
    return empty_deque

@pytest.fixture
def sample_33_array():
    return np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])

def test_empty(empty_deque: np.ndarray):
    """Test that an empty deque is empty"""
    assert empty_deque.size() == 0

def test_add(empty_deque: DequeArray):
    """Test addition of a single element"""
    empty_deque.append(np.random.rand(3, 3))
    assert empty_deque.size() == 1

def test_pop(empty_deque: DequeArray, sample_33_array: np.ndarray):
    """Test addition and retrieval of a single element"""
    empty_deque.append(sample_33_array)
    out: np.ndarray = empty_deque.pop()
    assert np.array_equal(out, sample_33_array)
    assert empty_deque.size() == 0

def test_add_100(empty_deque: DequeArray):
    "Test adding 100 elements"
    for _ in range(100):
        empty_deque.append(np.random.rand(3, 3))
    assert empty_deque.size() == 100

def test_mix_add_and_pop(loaded_deque: DequeArray):
    for _ in range(50):
        loaded_deque.pop()
    for _ in range(25):
        loaded_deque.append(np.random.rand(3, 3))
    assert loaded_deque.size() == 75

def test_empty_pop_raises(empty_deque: DequeArray):
    with pytest.raises(IndexError):
        empty_deque.pop()