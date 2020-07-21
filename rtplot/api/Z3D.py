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

class Z3D(RealTimePlot, Z3DInternal):
    """
    Live plot for 3D XYZ data. Non-blocking.
    """

    def __init__(self, seconds_to_show=None, linestyle='b-'):
        super().__init__(seconds_to_show, linestyle)
        self._internal_plot_class = Z3DInternal

    def update(self, xyzs):
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
            if not isinstance(xyzs, np.ndarray):
                xyzs = np.array(xyzs)

            (num_coords, num_lines) = rtplot.core.helpers.get_data_characteristics(xyzs)
            if num_coords != 3:
                raise Exception(
                    "Data provided does not contain three coordinates for every line")

            if self.seconds_to_show is not None:
                # If trail specified, send time of update as well
                self._queue.put((xyzs, time.time_ns()))
            else:
                # Else send only data
                self._queue.put(xyzs)
        except:
            print(
                "An error occurred in the data provided to 'update'. See more information below.")
            raise