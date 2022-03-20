"""
PlotServer.py
Contains the base class of the plot server, which handles routing.
"""

from rtplot.statics import Static, VLine
from rtplot.version import __version__
from .bounds import Bounds

import numpy as np
import time
import datetime
import matplotlib as mpl
from matplotlib import pyplot as plt
import matplotlib.animation as animation
from matplotlib.artist import Artist
from matplotlib.patches import Patch
from mpl_toolkits.mplot3d import Axes3D
import copy
from collections import deque
import multiprocessing

# Messaging
import zmq

# Typing
from typing import List

from rtplot.helpers import *
from .events import Event


class PlotServer:
    """
    Internal class that creates the plot and manages its
    animation. This is the base class for all such animations,
    and contains common attributes and methods for all such internal
    plots.
    """

    # Window title. FPS will be appended to end.
    window_title = f"rtplot {__version__}: "

    # Plot option defaults
    plot_option_defaults = {
        "tail_length": -1,
        "timeout": 3,
        "linestyle": [],
        "statics": [],
        "head_size": 10
    }


    def __init__(self, dims: int, **plot_options):

        # Add defaults if not present
        for (k, v) in self.plot_option_defaults.items():
            plot_options.setdefault(k, v)

        # Set style
        mpl.style.use("fivethirtyeight")

        # ZMQ socket
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)
        self.socket.bind("tcp://*:5555")

        self.dims: int = dims

        # Create figure for plotting
        self.fig, self.ax = plt.subplots(subplot_kw=plot_options)

        # Configure plot
        self.fig.subplots_adjust(bottom=0.15)  # Fix xlabel cutoff bug

        # How long of a tail to show
        # negative = Show all values
        self.tail_length: float = s2ns(plot_options["tail_length"])

        # How long before plot auto-closes (seconds)
        # negative = never timeout
        self.timeout: float = s2ns(plot_options["timeout"])

        # Time that data was last received
        self.time_last_recv: int  = time.time_ns()

        # Received first data yet?
        self.recvd_first_data: bool = False

        # Statics
        self.statics = self.generate_statics(plot_options["statics"])

        # Number of drawn lines
        self.n_lines: int = 0

        # Store reference to all lines here
        self.lines: List[Artist] = []

        # Store reference to line heads here
        self.line_heads: List[Artist] = []

        # List of linestyles
        self.linestyles: List[str] = list(plot_options.pop("linestyle", default=""))

        # Track the time the last frame was shown (for fps)
        self.time_last_frame_ns: int = 0

        # Track the time of the last bounds change (to avoid changing it too frequently)
        self.time_last_bounds_change: int  = time.time_ns()

        # Plot bounds
        self.bounds = Bounds(self.dims)

    @property
    def did_timeout(self) -> bool:
        return (time.time_ns() - self.time_last_recv) > s2ns(self.timeout)

    @property
    def drawables(self) -> List[Artist]:
        return self.lines + self.line_heads + self.statics

    def plot_init(self) -> None:
        """
        This function is called once before the animation starts to generate the
        clearframe, and is also called again when we force redraw the background
        by sending a resize event. It must be implemented in a subclass-specific
        manner.
        """
        # 1D is a special case
        if self.dims == 1:
            self.ax.set_xlabel("Seconds ago")
        # Do this in 2D
        elif self.dims >= 2:
            self.ax.set_xlabel("X")
            self.ax.set_ylabel("Y")
        # Plus this if 3D
        if self.dims == 3:
            self.ax.set_ylabel("Z")

        return self.lines + self.static_objects
    
    def update_plot_from_bounds(self) -> None:
        # 1D is a special case
        if self.dims == 1:
            self.ax.set_xlim(*self.bounds.t)
            self.ax.set_ylim(*self.bounds.x)
        # Do this in 2D
        elif self.dims >= 2:
            self.ax.set_xlim(*self.bounds.x)
            self.ax.set_ylim(*self.bounds.y)
        # Plus this if 3D
        if self.dims == 3:
            self.ax.set_zlim(*self.bounds.z)


    def update(self, frame_number) -> List[Artist]:
        """
        This is the superfunction that is called every time the animation updates.
        It is defined in order to perform any activities that should be done in the update
        of every subclass, such as updating the fps. Subclasses should NOT override this function.
        """

        # Check for messages from the parent process
        if not self.message_queue.empty():
            msg = self.message_queue.get()
            if msg == Event.REQUEST_KILL:
                self.kill()

        # Call the subclass-specific update function
        updated = self.plot_update(frame_number)
        

        # Update fps
        self.update_fps()

        # Return the subclass-specific update
        return updated

    def plot_update(self, frame_number: int) -> List[Artist]:
        """
        Everything that needs to be done in a single frame. It must be implemented
        in a subclass-specific manner.
        """
        raise NotImplementedError

    def start_animation(self, refresh_interval: int) -> None:
        """
        Starts the animation.
        """
        self.refresh_interval = refresh_interval  # milliseconds
        self.ani = animation.FuncAnimation(
            self.fig,
            self.update,
            init_func=self.plot_init,
            interval=refresh_interval,
            blit=True,
        )
        plt.show()

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

    def generate_statics(self, static_definitions: List[Static]) -> List[Artist]:
        """
        Takes the static definitions provided by the instantiating class and transforms
        them into real line objects that MPL can plot. These are stored and included as part
        of the background.
        """
        statics = []
        for s in static_definitions:
            artist = s.generate()
            if isinstance(artist, Patch):
                self.ax.add_patch(artist)
            statics.append(artist)
        return statics

    def update_fps(self) -> None:
        """
        Updates window title text with fps
        """
        current_time_ns = time.time_ns()
        delta_time = current_time_ns - self.time_last_frame_ns
        if delta_time == 0:
            fps = "∞"
        else:
            fps = round(1e9 / (current_time_ns - self.time_last_frame_ns), 2)
        self.fig.canvas.set_window_title(self.window_title + f"{fps} fps")
        self.time_last_frame_ns = current_time_ns
