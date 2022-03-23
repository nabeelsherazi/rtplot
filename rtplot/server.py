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
from typing import List, Union

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

    def __init__(self, port: int, dims: int, **plot_options):

        self.dims: int = dims

        # Set style
        mpl.style.use("fivethirtyeight")

        # ZMQ context
        self.context = zmq.Context()
        self.socket: zmq.Socket = self.context.socket(zmq.PAIR)
        self.socket.connect(f"tcp://localhost:{port}")

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

        # Received first data yet?
        self.recvd_first_data: bool = False

        # Number of drawn lines
        self.n_lines: int = 0

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

        # Data held here
        self.ts = deque()
        self.xs = deque()
        self.ys = deque()
        self.zs = deque()

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

    @property
    def num_lines(self) -> int:
        return len(self.lines)

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
    
    def initialize_lines(self, n: int) -> None:
        """
        Create n line objects, using fmts provided
        """
        while self.num_lines < n:
            # Create a new line
            # See if there's a fmt desired for this index, or just let MPL pick one
            if len(self.fmts) < self.num_lines:
                [new_line] = plt.plot([], [], self.fmts[self.num_lines])
            else:
                [new_line] = plt.plot([], [])
            self.lines.append(new_line)
            # Create a new "line head," which is just a line with a single point that will follow
            # the newest point of its associated line
            [new_line_head] = plt.plot([], [], marker='o', c=new_line.get_color(), markersize=self.head_size)
            self.line_heads.append(new_line_head)
        
        # Sanity check
        assert len(self.lines) == len(self.line_heads)


    def update(self, frame_number: int) -> List[Artist]:
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
        if msg == Event.REQUEST_KILL:
            self.kill()
        elif isinstance(msg, np.ndarray):
            # Client will ensure message is always an ndarray
            # Array will look like (for 1D):
            # [x1, x2, ..., xn]
            # And for 3D:
            # [[x1, y1, z1], [x2, y2, z2], ..., [xn, yn, zn]]
            self.ts.append(current_time_ns)
            if self.dims == 1:
                self.xs.append(msg)
            elif self.dims >= 2:
                self.xs.append(msg[:, 1])
                self.ys.append(msg[:, 2])
            if self.dims == 3:
                self.zs.append(msg[:, 3])
        
        # Prune data we don't need anymore
        # If tail length == 0, delta time will be 0 for the last added value
        # so only that one will remain
        if self.tail_length >= 0:
            while (current_time_ns - self.ts[0]) > self.tail_length:
                self.ts.popleft()
                if self.dims >= 1:
                    self.xs.popleft()
                if self.dims >= 2:
                    self.ys.popleft()
                if self.dims == 3:
                    self.zs.popleft()
            
        # Draw data
        for i in range(self.n_lines):
            line = self.lines[i]
            

        

        # Update fps
        self.update_title()

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
        """
        Kill all plots and release sockets
        """
        plt.close("all")
        self.context.destroy()
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
