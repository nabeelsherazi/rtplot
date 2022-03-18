# internal.py
# Contains classes related to the internal plots in rtplot. These classes
# are instantiated entirely within the main, user-facing classes.
# You should never need to instantiate one of these directly.

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


class XY(Internal.RealTimePlot_Internal):
    """
    Internal plot for XY
    """

    def __init__(self, data_queue, message_queue, seconds_to_show, timeout, linestyle, statics):

        super().__init__(data_queue, message_queue,
                         seconds_to_show, timeout, linestyle, statics)

        # Use deques for storing rolling data (optionally rolling)
        # Each element of this deque should be a (n_lines x 2) ndarray
        self.points = deque()

        self.is_trail_on = False
        self.seconds_to_show = seconds_to_show
        if self.seconds_to_show is not None:
            # If we want to only plot the last few seconds of data,
            # we need to store the time each data point was received at
            # too
            self.is_trail_on = True
            self.ts = deque()

        # Bounds
        self.current_side_length = 0
        self.last_redraw_frame_number = 0
        self.need_redraw = False
        self.num_frames_have_needed_redraw = 0

        # Statics
        self.static_definitions = statics
        self.generate_statics()

    def plot_init(self):
        plt.xlabel("X")
        plt.ylabel("Y")
        return self.line_heads + self.lines + self.static_objects

    def plot_update(self, frame_number):
        # Check for timeout
        current_time_ns = time.time_ns()
        if (self.queue.empty() and self.timeout is not None and not self.did_time_out):
            if current_time_ns - self.time_last_received_data >= self.timeout_ns:
                self.did_time_out = True
                raise SystemExit
            else:
                return self.line_heads + self.lines + self.static_objects
        else:
            # Read as much data as we can get from multiprocess queue
            while not self.queue.empty():
                data_point = self.queue.get()
                xys = data_point[0]
                if self.is_trail_on:
                    t = data_point[1]
                (data_n_coords, data_n_lines) = rtplot.core.helpers.get_data_characteristics(
                    xys)
                if self.n_lines is not None and data_n_lines != self.n_lines:
                    raise Exception(f"Inconsistent number of lines to plot: expected {self.n_lines} "
                                    f"but last update contained {data_n_lines} data points.")
                else:
                    # If number of lines isn't defined, infer it from the first update
                    self.n_lines = data_n_lines
                    # Create new line objects for the new data points
                    while len(self.lines) < self.n_lines:
                        # New lines will have auto linestyle
                        new_line, = plt.plot([], [])
                        new_line_head, = plt.plot(
                            [], [], marker='o', c=new_line.get_color(), markersize=10)
                        self.lines.append(new_line)
                        self.line_heads.append(new_line_head)
                self.points.append(xys)
                self.time_last_received_data = current_time_ns
                if self.is_trail_on:
                    self.ts.append(t)

        # Short circuit on if no data
        if len(self.xys) == 0 or len(self.ts) == 0:
            return self.line_heads + self.lines + self.static_objects

        if self.is_trail_on:
            current_time_ns = time.time_ns()
            # Remove from front if timestamp of oldest data is older than max seconds to show
            while (current_time_ns - self.ts[0]) > self.seconds_to_show_ns:
                self.points.popleft()
                self.ts.popleft()

        # These lists are unsorted *all* x and y data, for the purposes of bounds checking.
        # We will not use these otherwise unless there's only one line anyway (in which case
        # it doesn't matter)
        pts_data = np.array(self.points)
        if self.n_lines == 1:
            all_x_data = pts_data[:, 0]
            all_y_data = pts_data[:, 1]
        else:
            all_x_data = pts_data[:, :, 0]
            all_y_data = pts_data[:, :, 1]

        # Adjust bounds if needed
        bounds = self.get_data_bounds([all_x_data, all_y_data])

        # Get the axis with the longest length
        bounds.sort(key=lambda b: b["range"], reverse=True)
        longest_bound = bounds[0]

        min_side_length = abs(longest_bound["range"])

        # RULE: If lines go outside of the current bounds + a margin width, need a redraw
        # If all lines are inside of 75% of the current bounds, need a redraw
        # If we've needed a redraw for more than three seconds, do the redraw

        current_margin = 0.1 * self.current_side_length

        if min_side_length > (self.current_side_length + current_margin) or min_side_length < 0.75 * self.current_side_length:
            self.need_redraw = True
            self.num_frames_have_needed_redraw += 1
            # If the need is dire
            if min_side_length > (self.current_side_length + 3 * current_margin):
                # Screw the rules, redraw now
                margin = 0.1 * min_side_length
                plt.xlim(longest_bound["min"] - margin,
                         longest_bound["max"] + margin)
                plt.ylim(longest_bound["min"] - margin,
                         longest_bound["max"] + margin)
                self.current_side_length = min_side_length + margin
                self.force_redraw()
                self.need_redraw = False
                self.num_frames_have_needed_redraw = 0
        else:
            self.need_redraw = False
            self.num_frames_have_needed_redraw = 0

        secs_have_needed_redraw = self.num_frames_have_needed_redraw * \
            self.refresh_interval / 1000
        if secs_have_needed_redraw > 1.0 and self.need_redraw:
            # Redraw now
            margin = 0.1 * min_side_length
            plt.xlim(longest_bound["min"] - margin,
                     longest_bound["max"] + margin)
            plt.ylim(longest_bound["min"] - margin,
                     longest_bound["max"] + margin)
            self.current_side_length = min_side_length + margin
            self.force_redraw()
            self.need_redraw = False
            self.num_frames_have_needed_redraw = 0

        # Draw data
        if self.n_lines == 1:
            line = self.lines[0]
            line.set_data(all_x_data, all_y_data)
            line_head = self.line_heads[0]
            line_head.set_data(all_x_data[-1], all_y_data[-1])
        else:
            for i in range(self.n_lines):
                line_i = self.lines[i]
                line_head_i = self.line_heads[i]
                # Get time series of this line
                ix_data = pts_data[:, i, 0]
                iy_data = pts_data[:, i, 1]
                line_i.set_data(ix_data, iy_data)
                line_head_i.set_data(ix_data[-1], iy_data[-1])

        return self.line_heads + self.lines + self.static_objects
