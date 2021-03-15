# main.py
# Contains classes related to the external, user-facing plot API.
# Classes from here are what should be instantiated in your code.

import rtplot.helpers
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


class XY(Api.RealTimePlot):
    """
    Live plot for XY data. Non-blocking.
    """

    def __init__(self, seconds_to_show=None, timeout=None, linestyle='b-'):
        super().__init__(Internal.XY, seconds_to_show=seconds_to_show,
                         timeout=timeout, linestyle=linestyle)

    def update(self, xys):
        """
        Update the live plot with a new data point. If the number of concurrent lines to plot
        hasn't been specified yet (via multiple linestyles given), then the length of the first
        update will be used to infer.
        """
        try:
            if not self.is_started:
                raise Exception(
                    "Call to update before plot was started. Call start first.")
            # Coerce to numpy array
            if not isinstance(xys, np.ndarray):
                xys = np.array(xys)
            # There are two errors to catch here
            try:
                # If passed array is single column, this will raise IndexError
                num_coords = np.size(xys, 1)
                # If it's more than two columns, we have to raise here
                if num_coords != 2:
                    raise Exception(
                        "Number coordinates per line doesn't equal two.")
            except IndexError:
                if np.size(xys) != 2:
                    raise Exception(
                        "Number coordinates in passed array doesn't equal two.")

            if self.seconds_to_show is not None:
                # If trail specified, send time of update as well
                self._queue.put((xys, time.time_ns()))
            else:
                # Else send only data
                self._queue.put(xys)
        except:
            print(
                "An error occurred in the data provided to 'update'. See more information below.")
            raise
