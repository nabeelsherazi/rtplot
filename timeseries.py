import numpy as np
import time
import matplotlib
from matplotlib import pyplot as plt
import matplotlib.animation as animation
from matplotlib import style
from collections import deque
import multiprocessing

class TimeSeries():
    """
    Live plot for timeseries data. Non-blocking.
    """
    def __init__(self, seconds_to_show, linestyle='b-'):
        self.is_started = False
        self.refresh_interval = 100
        self.linestyle = linestyle
        self.seconds_to_show = seconds_to_show
    
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

    # START INTERNAL CLASS

    class TimeSeriesInternal():
        """
        INTERNAL: Internal class that creates the plot and manages its
        animation. This class is instantiated entirely within its own thread,
        and updates are passed to it via a multiprocessing queue.
        """
        def __init__(self, mp_queue, seconds_to_show, linestyle):

            # Queue reference for getting data from parent process
            self.queue = mp_queue

            # Set style
            style.use('fivethirtyeight')

            # Create figure for plotting
            fig, ax = plt.subplots()
            self.fig = fig
            self.ax = ax

            # Use deques for storing rolling timeseries
            self.ts = deque()
            self.ys = deque()

            self.seconds_to_show = seconds_to_show
            self.seconds_to_show_ns = seconds_to_show * 1E9

            # Create empty plot
            line, = plt.plot([], [], linestyle)

            # Store reference to line artist
            self.line = line

        def __plot_init(self):
            """
            Used in animation function call
            """
            self.ax.set_xlim(-self.seconds_to_show, 0)
            plt.xlabel("Seconds ago")
            self.ax.set_ylim('auto')
            return self.line,

        def __plot_update(self, frame_number):
            """
            This function is called every refresh_interval
            by MPL
            """

            # Read as much data as we can get from multiprocess queue 
            while not self.queue.empty():
                (t, y) = self.queue.get()
                self.ts.append(t)
                self.ys.append(y)
            
            current_time_ns = time.time_ns()

            # Remove from front if timestamp of oldest data is older than max seconds to show
            while (current_time_ns - self.ts[0]) / 1E9 > self.seconds_to_show:
                self.ts.popleft()
                self.ys.popleft()

            # Create y and t lists
            y_data = list(self.ys)
            t_data = []

            # Transform timestamps from nanoseconds to seconds
            for t in self.ts:
                seconds_ago = (t - current_time_ns) / 1E9
                t_data.append(seconds_ago)

            # Draw data
            self.line.set_data(t_data, y_data)
            return self.line,

        def start_animation(self, refresh_interval):
            """
            Animation starts here.
            """
            self.ani = animation.FuncAnimation(self.fig, self.__plot_update, init_func=self.__plot_init, interval=refresh_interval, blit=True)
            plt.show()
    
    # END INTERNAL CLASS
        
    def create_timeseries_plot(self, mp_queue):
        """
        Handles instantiating the internal plot
        """
        self.plot = self.TimeSeriesInternal(mp_queue, self.seconds_to_show, self.linestyle)
        self.plot.start_animation(self.refresh_interval)

    def set_options(self, refresh_interval=100):
        """
        Advanced options.
        """
        self.refresh_interval = refresh_interval

    def start(self):
        """
        Starts the live plotter!
        """
        self.queue = multiprocessing.Queue()
        self.is_started = True
        self.process = multiprocessing.Process(target=self.create_timeseries_plot, args=(self.queue, self.seconds_to_show, self.linestyle))
        self.process.start()

    def update(self, y):
        """
        Update the live plot with a new data point!
        """
        if not self.is_started:
            raise Exception("Call to update before plot was started. Call XY.start first.")
        self.queue.put((time.time_ns(), y))

    def quit(self):
        """
        End the live plotter.
        """
        self.process.terminate()
        self.is_started = False