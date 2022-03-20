from enum import Enum, unique

@unique
class Event(Enum):
    REQUEST_KILL = 1
    PLOT_ERROR = 2
    TIMED_OUT = 3
    DATA_ERROR = 4