# main.py
# Contains classes related to the external, user-facing plot API.
# Classes from here are what should be instantiated in your code.

import numpy as np
import time
import matplotlib
from matplotlib import pyplot as plt
import matplotlib.animation as animation
from matplotlib import style
from collections import deque
import multiprocessing

import rtplot.internal
import rtplot.helpers

class TimeSeries(RealTimePlot, TimeSeriesInternal):
    """
    Update the live plot with a new data point. If the number of concurrent lines to plot
    hasn't been specified yet (via multiple linestyles given), then the length of the first
    update will be used to infer.
    """

    def __init__(self, seconds_to_show=None, linestyle='b-'):
        super().__init__(seconds_to_show, linestyle)
        self._internal_plot_class = TimeSeriesInternal

    def update(self, y):
        if not self.is_started:
            raise Exception(
                "Call to update before plot was started. Call start first.")
        # Coerce to numpy array
        if not isinstance(y, np.ndarray):
            y = np.array(y)
        self._queue.put((time.time_ns(), y))