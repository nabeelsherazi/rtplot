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

import rtplot.api as Api
import rtplot.internal as Internal
import rtplot.helpers


class TimeSeries(Api.RealTimePlot):
    """
    Update the live plot with a new data point. If the number of concurrent lines to plot
    hasn't been specified yet (via multiple linestyles given), then the length of the first
    update will be used to infer.
    """

    def __init__(self, **plot_options):
        super().__init__(Internal.TimeSeries_Internal, **plot_options)

    def update(self, y):
        if not self.is_started:
            print(
                "Call to update before plot was started. Call start first.")
            return
        # Coerce to numpy array
        if not isinstance(y, np.ndarray):
            y = np.array(y)
        self._data_queue.put((time.time_ns(), y))
