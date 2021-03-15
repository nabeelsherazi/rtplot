# internal.py
# Contains classes related to the internal plots in rtplot. These classes
# are instantiated entirely within the main, user-facing classes.
# You should never need to instantiate one of these directly.

from rtplot.version import __version__

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

from rtplot.helpers import RtplotEvent


class RealTimePlot:
    """
    Internal class that creates the plot and manages its
    animation. This is the base class for all such animations,
    and contains common attributes and methods for all such internal
    plots.
    """

    def __init__(self, data_queue, message_queue, **plot_options):

        # Queue reference for getting data from parent process
        self.data_queue = data_queue
        self.message_queue = message_queue

        # Set style
        style.use('fivethirtyeight')

        # Create figure for plotting
        fig, ax = plt.subplots(subplot_kw=plot_options)
        self.fig = fig
        self.ax = ax
        self.fig.subplots_adjust(bottom=0.15)  # Fix xlabel cutoff bug
        self.fig.canvas.set_window_title(f"rtplot {__version__}: 0 fps")

        self.seconds_to_show = plot_options["seconds_to_show"]

        # How long before plot auto-closes
        # -1 = never timeout
        self.timeout = plot_options["timeout"]
        self.time_last_received_data = time.time_ns()
        self.did_time_out = False

        # Statics
        self.static_definitions = plot_options["statics"]
        self.static_objects = []

        # Number of drawn lines
        self.n_lines = None

        # Store reference to all lines here
        self.lines = []

        # Store reference to line heads, if needed, here
        self.line_heads = []

        # Check type of linestyle: if a list is passed,
        # we can expect multiline plotting and can set self.n_lines
        # now. If a string is passed, could be one or more, we don't know
        if isinstance(linestyle, list):
            self.n_lines = len(linestyle)
            for i_style in linestyle:
                # Make an empty plot
                i_line, = plt.plot([], [], i_style)
                self.lines.append(i_line)
                i_line_head, = plt.plot(
                    [], [], marker='o', c=i_line.get_color(), markersize=10)
                self.line_heads.append(i_line_head)
        else:
            line, = plt.plot([], [], linestyle)
            line_head, = plt.plot([], [], marker='o',
                                  c=line.get_color(), markersize=10)
            self.lines.append(line)
            self.line_heads.append(line_head)

        # Track how many seconds since last frame (for fps)
        self.last_finished_frame_time = 0.00

    @property
    def seconds_to_show_ns(self):
        if self.seconds_to_show is not None:
            return self.seconds_to_show * 1E9
        else:
            return None

    @property
    def timeout_ns(self):
        if self.timeout is not None:
            return self.timeout * 1E9
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
                        raise Warning(
                            "Custom linestyle for static point includes directive to plot as line. This point won't be visible.")
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

        # Check for messages from the parent process
        if not self.message_queue.empty():
            msg = self.message_queue.get()
            if msg == RtplotEvent.REQUEST_KILL:
                self.kill()

        # Call the subclass-specific update function
        updated = self.plot_update(frame_number)

        # Update fps
        current_time_ns = time.time_ns()
        delta_time = (current_time_ns - self.last_finished_frame_time)
        if delta_time == 0:
            fps = "∞"
        else:
            fps = round(1E9 / (current_time_ns -
                               self.last_finished_frame_time), 2)
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
        self.refresh_interval = refresh_interval  # milliseconds
        self.ani = animation.FuncAnimation(
            self.fig, self.plot_update_master, init_func=self.plot_init, interval=refresh_interval, blit=True)
        plt.show()

    @staticmethod
    def min_and_max(data):
        """
        Return the min and max of a given numpy array, as a tuple
        """
        return (np.amin(data), np.amax(data))

    @staticmethod
    def get_data_bounds(data_list):
        bounds = []
        for data in data_list:
            (dmin, dmax) = RealTimePlot.min_and_max(data)
            drange = dmax - dmin
            bounds.append({"range": drange, "min": dmin, "max": dmax})
        return bounds

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

    def kill(self):
        plt.close("all")
        raise SystemExit
