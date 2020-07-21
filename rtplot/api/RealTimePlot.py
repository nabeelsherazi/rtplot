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

class RealTimePlot:
    """
    Base class for the user facing interface to create a real time plot.
    """

    def __init__(self, seconds_to_show=None, linestyle='b-', *args, **kwargs):
        # Gotta put in the internal plot class here when you subclass
        self._internal_plot_class = None
        self.is_started = False
        self._seconds_to_show = seconds_to_show
        self._refresh_rate = 10
        self._linestyle = linestyle
        self.statics = []

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
            raise Exception(
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
            raise Exception(
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
            raise Exception(
                "Cannot change value while plot is running. Quit plot to change values, then restart.")

    def add_static(self, static_name, **kwargs):
        valid_statics = ["point", "circle", "rectangle", "vline", "hline"]
        if static_name not in valid_statics:
            raise Exception(
                "Invalid static requested. See help on this function.")
        new_static = {}
        if static_name == "point":
            new_static = rtplot.core.helpers.point(**kwargs)
        elif static_name == "circle":
            new_static = rtplot.core.helpers.circle(**kwargs)
        elif static_name == "rectangle":
            new_static = rtplot.core.helpers.rectangle(**kwargs)
        elif static_name == "vline":
            new_static = rtplot.core.helpers.vline(**kwargs)
        elif static_name == "hline":
            new_static = rtplot.core.helpers.hline(**kwargs)
        self.statics.append(new_static)

    def _create_internal_plot(self, mp_queue):
        """
        Handles instantiating the internal plot. End users should not need to call this ever, it's
        done in the start function.
        """
        self._plot = self._internal_plot_class(
            mp_queue, self.seconds_to_show, self.linestyle, self.statics)
        # Convert Hz to milliseconds
        self._plot.start_animation(int(1 / self._refresh_rate * 1E3))

    def start(self):
        """
        Starts the live plotter!
        """
        try:
            self._queue = multiprocessing.Queue()
            self.is_started = True
            self._process = multiprocessing.Process(
                target=self._create_internal_plot, args=(self._queue,))
            self._process.start()
        except RuntimeError:
            print("""If you're seeing this error, you probably forgot to wrap your code in a `if __name == "__main__"` guard.""")
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
        self._process.terminate()
        self.is_started = False