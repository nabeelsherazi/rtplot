from enum import Enum, unique, auto

@unique
class Event(Enum):
    HEARTBEAT = auto()
    REQUEST_CLOSE = auto()
    TIMED_OUT = auto()
    PLOT_CLOSED = auto()