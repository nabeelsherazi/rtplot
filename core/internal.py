# internal.py
# Contains classes related to the internal plots in rtplot. These classes
# are instantiated entirely within the main, user-facing classes.
# You should never need to instantiate one of these directly.

from . import __version__
import numpy as np
import time
import matplotlib
from matplotlib import pyplot as plt
import matplotlib.animation as animation
from matplotlib import style
import copy
from collections import deque
import multiprocessing

class InternalRealTimePlot:
    """
    Internal class that creates the plot and manages its
    animation. This is the base class for all such animations,
    and contains common attributes and methods for all such internal
    plots.
    """
    def __init__(self, mp_queue, seconds_to_show, linestyle, statics, *args, **kwargs):

        # Queue reference for getting data from parent process
        self.queue = mp_queue

        # Set style
        style.use('fivethirtyeight')

        # Create figure for plotting
        fig, ax = plt.subplots()
        self.fig = fig
        self.ax = ax
        self.fig.subplots_adjust(bottom=0.15) # Fix xlabel cutoff bug
        self.fig.canvas.set_window_title(f"rtplot {__version__}: 0 fps")

        self.seconds_to_show = seconds_to_show

        # Statics
        self.static_definitions = statics
        self.static_objects = []

        # Number of drawn lines
        self.n_lines = None

        # Store reference to all lines here
        self.lines = []

        # Check type of linestyle: if a list is passed,
        # we can expect multiline plotting and can set self.n_lines
        # now. If a string is passed, could be one or more, we don't know
        if isinstance(linestyle, list):
            self.n_lines = len(linestyle)
            for i_style in linestyle:
                # Make an empty plot
                i_line, = plt.plot([], [], i_style)
                self.lines.append(i_line)
        else:
            line, = plt.plot([], [], linestyle)
            self.lines.append(line)
        
        # Track how many seconds since last frame (for fps)
        self.last_finished_frame_time = 0.00

    @property
    def seconds_to_show_ns(self):
        if self.seconds_to_show is not None:
            return self.seconds_to_show * 1E9
        else:
            return None

    def plot_init(self):
        """
        This function is called once before the animation starts to generate the
        clearframe, and is also called again when we force redraw the background
        by sending a resize event. It must be implemented in a subclass-specific
        manner.
        """
        raise NotImplementedError

    def generate_statics(self):
        """
        Takes the static definitions provided by the instantiating class and transforms
        them into real line objects that MPL can plot. These are stored and included as part
        of the background.
        """
        for static_def in self.static_definitions:
            static_name = next(iter(static_def))
            params = static_def[static_name]

            if static_name == "point":
                xy = params.pop("xy")
                if "linestyle" in params:
                    if '-' in params["linestyle"]:
                        raise Warning("Custom linestyle for static point includes directive to plot as line. This point won't be visible.")
                    static_pt, = plt.plot(xy[0], xy[1], params["linestyle"])
                else:
                    static_pt, = plt.plot(xy[0], xy[1], 'x')
                self.static_objects.append(static_pt)
            
            elif static_name == "circle":
                xy = params.pop("xy")
                c = plt.Circle(xy, **params)
                self.ax.add_patch(c)
                self.static_objects.append(c)
            
            elif static_name == "rectangle":
                xy = params.pop("xy")
                width = params.pop("width")
                height = params.pop("height")
                rect = plt.Rectangle(xy, width, height, **params)
                self.ax.add_patch(rect)
                self.static_objects.append(rect)
            
            elif static_name == "vline":
                x = params.pop("x")
                line = plt.axvline(x, 0, 1, **params)
                self.static_objects.append(line)
            
            elif static_name == "hline":
                y = params.pop("y")
                line = self.ax.axhline(y, 0, 1, **params)
                self.static_objects.append(line)

    def plot_update_master(self, frame_number):
        """
        This is the superfunction that is called every time the animation updates.
        It is defined in order to perform any activities that should be done in the update
        of every subclass, such as updating the fps. Subclasses should NOT override this function.
        """

        # Call the subclass-specific update function
        updated = self.plot_update(frame_number)

        # Update fps
        current_time_ns = time.time_ns()
        delta_time = (current_time_ns - self.last_finished_frame_time)
        if delta_time == 0:
            fps = "∞"
        else:
            fps = round(1E9 / (current_time_ns - self.last_finished_frame_time), 2)
        self.fig.canvas.set_window_title(f"rtplot {__version__}: {fps} fps")
        self.last_finished_frame_time = current_time_ns

        # Return the subclass-specific update
        return updated

    def plot_update(self, frame_number):
        """
        Everything that needs to be done in a single frame. It must be implemented
        in a subclass-specific manner.
        """
        raise NotImplementedError

    def start_animation(self, refresh_interval):
        """
        Starts the animation.
        """
        self.refresh_interval = refresh_interval # milliseconds
        self.ani = animation.FuncAnimation(self.fig, self.plot_update_master, init_func=self.plot_init, interval=refresh_interval, blit=True)
        plt.show()
    
    def min_and_max(self, data):
        """
        Return the min and max of a given numpy array, as a tuple
        """
        return (np.amin(data), np.amax(data))
    
    def force_redraw(self):
        """
        Force the canvas to perform a full redraw, including the background.
        We use this when the data starts to go outside of the current axes, as
        the current matplotlib has a bug where the background clearframe
        is not updated when axes change, even though they should be. So we do some
        clever stuff with this.
        """
        self.ani._init_func = None
        self.fig.canvas.resize_event()


class TimeSeriesInternal(InternalRealTimePlot):
    """
    Internal plot for TimeSeries
    """
    def __init__(self, mp_queue, seconds_to_show, linestyle, statics):
        super().__init__(mp_queue, seconds_to_show, linestyle, statics)

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
                    new_line, = plt.plot([], []) # New lines will have auto linestyle
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
        if np.size(y_data, 1) == 1:
            newest_quarter_of_data = y_data[three_quarter_point:]
        else:
            newest_quarter_of_data = y_data[three_quarter_point:, :]
        # ... if more than half of *any* line is out of bounds,
        outside_bounds_mask = (newest_quarter_of_data < self.current_ymin) | (newest_quarter_of_data > self.current_ymax)
        max_frac_outside = 0.0
        for i in range(self.n_lines):
            frac_outside = outside_bounds_mask[:, i].sum() / outside_bounds_mask[:, i].size
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


class XYInternal(InternalRealTimePlot):
    """
    Internal plot for XY
    """
    def __init__(self, mp_queue, seconds_to_show, linestyle, statics):

        super().__init__(mp_queue, seconds_to_show, linestyle, statics)

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
        return self.lines + self.static_objects

    def plot_update(self, frame_number):
        # Read as much data as we can get from multiprocess queue 
        while not self.queue.empty():
            data_point = self.queue.get()
            xys = data_point[0]
            if self.is_trail_on:
                t = data_point[1]
            if self.n_lines is not None and np.size(xys, 0) != self.n_lines:
                raise Exception(f"Inconsistent number of lines to plot: expected {self.n_lines} "
                                f"but last update contained {np.size(xys, 0)} data points.")
            else:
                # If number of lines isn't defined, infer it from the first update
                self.n_lines = np.size(xys, 0)
                # Create new line objects for the new data points
                while len(self.lines) < self.n_lines:
                    new_line, = plt.plot([], []) # New lines will have auto linestyle
                    self.lines.append(new_line)
            self.points.append(xys)
            if self.is_trail_on:
                self.ts.append(t)
        
        if self.is_trail_on:
            current_time_ns = time.time_ns()
            # Remove from front if timestamp of oldest data is older than max seconds to show
            while (current_time_ns - self.ts[0]) > self.seconds_to_show_ns:
                self.points.popleft()
                self.ts.popleft()

        # These lists are unsorted *all* x and y data, for the purposes of bounds checking.
        # We will not use not use these outside of that purpose
        pts_data = np.array(self.points)
        if self.n_lines == 1:
            all_x_data = pts_data[:, 0]
            all_y_data = pts_data[:, 1]
        else:
            all_x_data = pts_data[:, :, 0]
            all_y_data = pts_data[:, :, 1]

        # Adjust bounds if needed
        (xmin, xmax) = self.min_and_max(all_x_data)
        (ymin, ymax) = self.min_and_max(all_y_data)
        x_axis_range = xmax - xmin
        y_axis_range = ymax - ymin

        if y_axis_range > x_axis_range:
            min_side_length = abs(y_axis_range)
            longer_side_is_y = True
        else:
            min_side_length = abs(x_axis_range)
            longer_side_is_y = False

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
                if longer_side_is_y:
                    plt.xlim(ymin - margin , ymax + margin)
                    plt.ylim(ymin - margin, ymax + margin)
                else:
                    plt.xlim(xmin - margin, xmax + margin)
                    plt.ylim(xmin - margin, xmax + margin)
                self.current_side_length = min_side_length + margin
                self.force_redraw()
                self.need_redraw = False
                self.num_frames_have_needed_redraw = 0
        else:
            self.need_redraw = False
            self.num_frames_have_needed_redraw = 0

        secs_have_needed_redraw = self.num_frames_have_needed_redraw * self.refresh_interval / 1000
        if secs_have_needed_redraw > 1.0 and self.need_redraw:
            # Redraw now
            margin = 0.1 * min_side_length
            if longer_side_is_y:
                plt.xlim(ymin - margin , ymax + margin)
                plt.ylim(ymin - margin, ymax + margin)
            else:
                plt.xlim(xmin - margin, xmax + margin)
                plt.ylim(xmin - margin, xmax + margin)
            self.current_side_length = min_side_length + margin
            self.force_redraw()
            self.need_redraw = False
            self.num_frames_have_needed_redraw = 0

        # Draw data
        if self.n_lines == 1:
            line = self.lines[0]
            line.set_data(all_x_data, all_y_data)
        else:
            for i in range(self.n_lines):
                line_i = self.lines[i]
                # Get time series of this line
                ix_data = pts_data[:, i, 0]
                iy_data = pts_data[:, i, 1]
                line_i.set_data(ix_data, iy_data)

        return self.lines + self.static_objects