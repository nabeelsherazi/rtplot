"""
PlotServer.py
Contains the base class of the plot server, which handles routing.
"""

# Array will look like (for 1D):
# [x1, x2, ..., xn]
# And for 3D:
# [[x1, y1, z1], [x2, y2, z2], ..., [xn, yn, zn]]

from rtplot.statics import Static, VLine
from rtplot.version import __version__
from .bounds import Bounds
from .npdeque import DequeArray
from .logger import logger

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
import atexit

# Messaging
import zmq

# Typing
from typing import Deque, List, NoReturn, Union

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

    def __init__(self, port: int, dims: int, num_lines: int, **plot_options):

        self.dims: int = dims
        self.num_lines: int = num_lines
        self.port = port

        # Set style
        mpl.style.use("fivethirtyeight")

        # Need to pop off all non-MPL items from the plot_options before passing
        # or it'll error

        # How long of a tail to show
        # negative = Show all values
        self.tail_length: float = s2ns(plot_options.pop("tail_length", default=-1))

        # How long before plot auto-closes (seconds)
        # negative = never timeout
        self.timeout: float = s2ns(plot_options.pop("timeout", default=3.0))

        # Statics
        self.statics: List[Static] = self.generate_statics(plot_options["statics"], default=[])

        # List of line format strings
        self.fmts: List[str] = list(plot_options.pop("fmts", default=[]))

        self.head_size: int = plot_options.pop("head_size", default=10)

        # Create figure for plotting
        self.fig, self.ax = plt.subplots(subplot_kw=plot_options)

        # Configure plot
        self.fig.subplots_adjust(bottom=0.15)  # Fix xlabel cutoff bug

        # Time that data was last received
        self.time_last_recv: int  = time.time_ns()

        # Store reference to all lines here
        self.lines: List[Artist] = []

        # Store reference to line heads here
        self.line_heads: List[Artist] = []

        # Track the time the last frame was shown (for fps)
        self.time_last_frame_ns: int = 0

        # Track the time of the last bounds change (to avoid changing it too frequently)
        self.time_last_bounds_change: int  = time.time_ns()

        # Plot bounds
        self.bounds = Bounds(self.dims)

        # Create data deque
        self.data = DequeArray(self.dims, self.num_lines)

    @property
    def did_timeout(self) -> bool:
        # Negative = never time out
        if self.timeout < 0:
            return False
        else:
            return (time.time_ns() - self.time_last_recv) > s2ns(self.timeout)

    @property
    def drawables(self) -> List[Artist]:
        return self.lines + self.line_heads + self.statics

    def init(self) -> None:
        # Initialize ZMQ
        try:
            self.init_socket()
        except:
            self.kill()
        # Initialize lines and line heads
        self.init_lines()

    def init_socket(self) -> None:
        """Initialize ZMQ context and connect."""
        # ZMQ context
        self.context = zmq.Context()
        self.socket: zmq.Socket = self.context.socket(zmq.PAIR)
        self.socket.connect(f"tcp://127.0.0.1:{self.port}")

    def init_lines(self) -> None:
        """Initialize line objects and line heads."""
        for next_line_ix in range(self.num_lines):
            # Create a new line
            # See if there's a fmt desired for this index, or just let MPL pick one
            if len(self.fmts) < next_line_ix:
                [new_line] = plt.plot([], [], self.fmts[next_line_ix])
            else:
                [new_line] = plt.plot([], [])
            self.lines.append(new_line)
            # Create a new "line head," which is just a line with a single point that will follow
            # the newest point of its associated line
            [new_line_head] = plt.plot([], [], marker='o', c=new_line.get_color(), markersize=self.head_size)
            self.line_heads.append(new_line_head)
        # Sanity check
        assert len(self.lines) == len(self.line_heads)

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
    
    def update_plot_lims_from_bounds(self) -> None:
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

    def update(self) -> List[Artist]:
        """
        This is the superfunction that is called every time the animation updates.
        It is defined in order to perform any activities that should be done in the update
        of every subclass, such as updating the fps. Subclasses should NOT override this function.
        """

        # Check for timeout
        if self.did_time_out:
            self.socket.send_pyobj(Event.TIMED_OUT)
            self.kill()

        # Get a message
        msg: Union[Event, np.ndarray] = self.socket.recv_pyobj()
        # Record time
        current_time_ns = time.time_ns()
        self.time_last_recv = current_time_ns

        # Parse message
        if msg == Event.HEARTBEAT:
            return self.lines + self.line_heads + self.statics
        elif msg == Event.REQUEST_CLOSE:
            self.kill()
        elif isinstance(msg, np.ndarray):
            self.data.append(msg)
        else:
            logger.error(f"Received object of unknown type: {repr(msg)}")
        
        # Prune data we don't need anymore
        if self.tail_length >= 0:
            while (current_time_ns - self.data[0]) > self.tail_length: # Note ">" here vs. ">=" above
                self.data.popleft()
            
        # Draw data
        self.draw()

        # Update fps in title
        self.update_title()

        return self.lines + self.line_heads + self.statics

    def draw(self) -> None:
        """Draw lines and line heads. Seperated out for mocking purposes."""
        # TODO: Splitting into two functions, one for lines and one for line heads,
        # would both improve cache locality, and make it easier to turn off line heads.
        # But it seems like a premature optimization without measurement.
        for i in range(self.num_lines):
            line, head = self.lines[i], self.line_heads[i]
            # In 1D (special case), we use the timestamps (column 0) for the plot's X data
            # the data (column 1) is sent to the plot's Y data
            if self.dims == 1:
                line.set_data(self.data[:, 0, i], self.data[:, 1, i])
                head.set_data(self.data[0, 0, i], self.data[0, 1, i])
            # In 2D and 3D, we set the X data (column 1) and Y data (column 2) as expected
            elif self.dims >= 2:
                line.set_data(self.data[:, 1, i], self.data[:, 2, i])
                head.set_data(self.data[0, 1, i], self.data[0, 2, i])
            # But in 3D, we have to use set_3d_properties for Z data (column 3)
            if self.dims == 3:
                line.set_3d_properties(self.data[:, 3, i])
                head.set_3d_properties(self.data[0, 3, i])


    def start_animation(self, refresh_interval: int) -> None:
        """Starts the animation."""
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

    @atexit.register
    def cleanup(self) -> None:
        """Close all plots and release sockets."""
        plt.close("all")
        self.socket.send_pyobj(Event.PLOT_CLOSED)
        self.context.destroy()

    def kill(self) -> NoReturn:
        """Cleanup and close out."""
        self.cleanup()
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

    def update_title(self) -> None:
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
