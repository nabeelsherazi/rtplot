# internal.py
# Contains classes related to the internal plots in rtplot. These classes
# are instantiated entirely within the main, user-facing classes.
# You should never need to instantiate one of these directly.

from .version import __version__

import numpy as np
import time
import matplotlib
from matplotlib import pyplot as plt
import matplotlib.animation as animation
from matplotlib import style
from mpl_toolkits.mplot3d import Axes3D
import copy
from collections import deque
import multiprocessing

import rtplot.internal as Internal
import rtplot.helpers

class TimeSeries(Internal.RealTimePlot):
    """
    Internal plot for TimeSeries
    """

    def __init__(self, mp_queue, seconds_to_show, timeout, linestyle, statics):
        super().__init__(mp_queue, seconds_to_show, timeout, linestyle, statics)

        # Use deques for storing rolling timeseries
        self.ts = deque()
        self.ys = deque()

        # Store current bounds
        self.current_tmin = -10.00
        self.current_ymin = 0.00
        self.current_ymax = 0.00

        # Generate statics
        self.generate_statics()

    def plot_init(self):
        if self.seconds_to_show is not None:
            self.ax.set_xlim(-self.seconds_to_show, 0)
        else:
            self.ax.set_xlim(self.current_tmin, 0)
        plt.xlabel("Seconds ago")
        (self.current_tmin, _) = self.ax.get_xlim()
        (self.current_ymin, self.current_ymax) = self.ax.get_ylim()
        return self.lines + self.static_objects

    def plot_update(self, frame_number):

        # Read as much data as we can get from multiprocess queue
        while not self.queue.empty():
            (t, y) = self.queue.get()
            self.ts.append(t)
            # If the number of lines is already defined, check new data
            # consistency with it
            if self.n_lines is not None and y.size != self.n_lines:
                raise Exception(f"Inconsistent number of lines to plot: expected {self.n_lines} "
                                f"but last update only contained {y.size} data points.")
            else:
                # If number of lines isn't defined, infer it from the first update
                self.n_lines = y.size
                # Create new line objects for the new data points
                while len(self.lines) < self.n_lines:
                    # New lines will have auto linestyle
                    new_line, = plt.plot([], [])
                    self.lines.append(new_line)
            self.ys.append(y)

        current_time_ns = time.time_ns()

        # If we're only showing the trail
        if self.seconds_to_show is not None:
            # Remove from front if timestamp of oldest data is older than max seconds to show
            while (current_time_ns - self.ts[0]) > self.seconds_to_show_ns:
                self.ts.popleft()
                self.ys.popleft()

        # Create y and t lists
        y_data = np.array(self.ys)
        t_data = np.zeros(len(self.ts))

        # Transform timestamps from nanoseconds to seconds
        for i in range(len(self.ts)):
            seconds_ago = (self.ts[i] - current_time_ns) / 1E9
            t_data[i] = seconds_ago

        need_redraw = False
        # Adjust Y axis if needed
        (ymin, ymax) = self.min_and_max(y_data)
        # Rule: within the newest quarter of data ...
        three_quarter_point = int(3 * np.size(y_data, 0) / 4)
        if self.n_lines == 1:
            newest_quarter_of_data = y_data[three_quarter_point:]
        else:
            newest_quarter_of_data = y_data[three_quarter_point:, :]
        # ... if more than half of *any* line is out of bounds,
        outside_bounds_mask = (newest_quarter_of_data < self.current_ymin) | (
            newest_quarter_of_data > self.current_ymax)
        max_frac_outside = 0.0
        for i in range(self.n_lines):
            frac_outside = outside_bounds_mask[:, i].sum(
            ) / outside_bounds_mask[:, i].size
            if frac_outside > max_frac_outside:
                max_frac_outside = frac_outside
        if max_frac_outside >= 0.5:
            # ... then adjust the axis
            margin = 0.1 * (ymax - ymin)
            self.ax.set_ylim(ymin - margin, ymax + margin)
            need_redraw = True
            self.current_ymin = ymin - margin
            self.current_ymax = ymax + margin

        if self.seconds_to_show is None and t_data[0] < self.current_tmin:
            self.current_tmin -= 5
            self.ax.set_xlim(self.current_tmin, 0)
            need_redraw = True

        if need_redraw:
            self.force_redraw()

        # Draw data
        for i in range(self.n_lines):
            current_line = self.lines[i]
            current_line.set_data(t_data, y_data[:, i])

        # Update fps
        fps = 1E9 / (current_time_ns - self.last_finished_frame_time)
        self.fig.canvas.set_window_title(f"rtplot {__version__}: {fps} fps")
        self.last_finished_frame_time = current_time_ns

        return self.lines + self.static_objects