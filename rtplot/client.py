# main.py
# Contains classes related to the external, user-facing plot API.
# Classes from here are what should be instantiated in your code.

import numpy as np
import time
import matplotlib as mpl
from matplotlib import pyplot as plt
import matplotlib.animation as animation
from matplotlib import style
from collections import deque
import multiprocessing

# Messaging
import zmq

import rtplot.internal as Internal
import rtplot.helpers
from rtplot.helpers import RtplotEvent


class PlotClient:
    """
    Base class for the user facing interface to create a real time plot.
    """

    def __init__(self, dims: int, **plot_options):
        # Check dimension valid
        if not 1 <= dims <= 3:
            raise ValueError(f"Plot dimension must be between 1 and 3, but received: {dims}")

        self._internal_plot_type = internal_plot_type

        self._timeout = plot_options.setdefault("timeout", 10)
        self._seconds_to_show = plot_options.setdefault("seconds_to_show", 10)
        self._refresh_rate = plot_options.setdefault("refresh_rate", 10)
        self._linestyle = plot_options.setdefault("linestyle", 'b-')

        # setdefault above inserts the keys if needed so this is fully up to date
        self.plot_options = plot_options
        self.statics = []
        # Link statics to plot options so it's passed down to internal plot
        # when it gets updated by add_statics
        self.plot_options["statics"] = self.statics

        # Is the plot running
        self.is_started = False

    def __enter__(self):
        """
        Allow usage in 'with' statements.
        """
        self.start()
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        """
        Allow usage in 'with' statements.
        """
        self.quit()
        if exception_type:
            print("Plot quit unexpectedly.")
            print(f"{exception_type} : {exception_value}")
            print(traceback)
        return True  # Suppress exception

    @property
    def seconds_to_show(self):
        """
        How many seconds of trailing data to show. Default None means show all data and expand
        axes as necessary.
        """
        return self._seconds_to_show

    @seconds_to_show.setter
    def seconds_to_show(self, value):
        if not self.is_started:
            self._seconds_to_show = value
        else:
            print(
                "Cannot change value while plot is running. Quit plot to change values, then restart.")

    @property
    def linestyle(self):
        """
        Line style of plot, passed directly to MPL. Can be either a single string
        or a list of strings. If the latter, the length of the string will be used
        to infer the number of lines you're trying to plot. If you only supply one
        string though, you can still add more lines when you send the first update
        (they'll just have auto linestyles)
        """
        return self._linestyle

    @linestyle.setter
    def linestyle(self, value):
        if not self.is_started:
            self._linestyle = value
        else:
            print(
                "Cannot change value while plot is running. Quit plot to change values, then restart.")

    @property
    def refresh_rate(self):
        """
        Refresh rate of the animation in Hz. Default 10 Hz.
        """
        return self._refresh_rate

    @refresh_rate.setter
    def refresh_rate(self, value):
        if not self.is_started:
            self._refresh_rate = value
        else:
            print(
                "Cannot change value while plot is running. Quit plot to change values, then restart.")

    def add_static(self, static_name, **kwargs):
        if self.is_started:
            print(
                "Statics added while plot is running will not appear unless plot is quit and restarted.")
        valid_statics = ["point", "circle", "rectangle", "vline", "hline"]
        if static_name not in valid_statics:
            print(
                "Invalid static requested. See help on this function.")
        new_static = {}
        if static_name == "point":
            new_static = rtplot.helpers.point(**kwargs)
        elif static_name == "circle":
            new_static = rtplot.helpers.circle(**kwargs)
        elif static_name == "rectangle":
            new_static = rtplot.helpers.rectangle(**kwargs)
        elif static_name == "vline":
            new_static = rtplot.helpers.vline(**kwargs)
        elif static_name == "hline":
            new_static = rtplot.helpers.hline(**kwargs)
        self.statics.append(new_static)

    def _create_internal_plot(self, data_queue, message_queue):
        """
        Handles instantiating the internal plot. End users should not need to call this ever, it's
        done in the start function.
        """

        self._plot = self._internal_plot_type(
            data_queue, message_queue, **self.plot_options)
        # Convert Hz to milliseconds
        self._plot.start_animation(int(1 / self._refresh_rate * 1E3))

    def start(self):
        """
        Starts the live plotter!
        """
        try:
            self._data_queue = multiprocessing.Queue()
            self._message_queue = multiprocessing.Queue()
            self._process = multiprocessing.Process(
                target=self._create_internal_plot, args=(self._data_queue, self._message_queue))
            self._process.daemon = True
            self._process.start()
            self.is_started = True
        except RuntimeError:
            print("""If you're seeing this error, you probably forgot to wrap your code in a `if __name == "__main__"` guard.""")
            self.quit()
            raise SystemExit
        except:
            print("Error in starting plot.")
            self.quit()
            raise SystemExit

    def update(self, data):
        """
        Update the live plot with a new data point. If the number of concurrent lines to plot
        hasn't been specified yet (via multiple linestyles given), then the length of the first
        update will be used to infer.
        """
        raise NotImplementedError

    def quit(self):
        """
        End the live plotter.
        """
        print("Closing plot")
        self._message_queue.put(RtplotEvent.REQUEST_KILL)
        time.sleep(1)
        # Force kill if necessary
        if self._process.is_alive():
            self._process.terminate()
        self._data_queue.close()
        self._message_queue.close()
        self.is_started = False
