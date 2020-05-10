import numpy as np
import time
import matplotlib
from matplotlib import pyplot as plt
import matplotlib.animation as animation
from matplotlib import style
from collections import deque
import multiprocessing

class XY():
    """
    Live plot for XY data. Non-blocking.
    """
    def __init__(self, trail_seconds=-1, linestyle='b-'):
        self.is_started = False
        self.refresh_interval = 100
        self.linestyle = linestyle
        self.trail_seconds = trail_seconds
    
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

    class XYInternal():
        """
        INTERNAL: Internal class that creates the plot and manages its
        animation. This class is instantiated entirely within its own thread,
        and updates are passed to it via a multiprocessing queue.
        """
        def __init__(self, mp_queue, trail_seconds, linestyle):

            # Queue reference for getting data from parent process
            self.queue = mp_queue

            # Set style
            style.use('fivethirtyeight')

            # Create figure for plotting
            fig, ax = plt.subplots()
            self.fig = fig
            self.ax = ax

            # Use deques for storing rolling data (optionally rolling)
            self.xs = deque()
            self.ys = deque()
            
            self.is_trail_on = False
            self.trail_seconds = trail_seconds
            if self.trail_seconds != -1:
                # If we want to only plot the last few seconds of data,
                # we need to store the time each data point was received at
                # too
                self.is_trail_on = True
                self.ts = deque()
                self.trail_seconds_ns = trail_seconds * 1E9

            # Create empty plot
            line, = plt.plot([], [], linestyle)

            # Store reference to line artist
            self.line = line

        def __plot_init(self):
            """
            Used in animation function call
            """
            return self.line,

        def __plot_update(self, frame_number):
            """
            This function is called every refresh_interval
            by MPL
            """

            # Read as much data as we can get from multiprocess queue 
            while not self.queue.empty():
                data_point = self.queue.get()
                self.xs.append(data_point[0])
                self.ys.append(data_point[1])
                if self.is_trail_on:
                    self.ts.append(data_point[2])
            
            if self.is_trail_on:
                current_time_ns = time.time_ns()
                # Remove from front if timestamp of oldest data is older than max seconds to show
                while (current_time_ns - self.ts[0]) > self.trail_seconds_ns:
                    self.xs.popleft()
                    self.ys.popleft()
                    self.ts.popleft()

            # Create x and y lists
            y_data = list(self.ys)
            x_data = list(self.xs)

            # Adjust bounds if needed
            max_value = max(x_data + y_data)
            min_value = min(x_data + y_data)
            square_bound_side_length = max((max_value, abs(min_value)))
            plt.xlim(-square_bound_side_length, square_bound_side_length)
            plt.ylim(-square_bound_side_length, square_bound_side_length)

            # Draw data
            self.line.set_data(x_data, y_data)
            return self.line,

        def start_animation(self, refresh_interval):
            """
            Animation starts here.
            """
            self.ani = animation.FuncAnimation(self.fig, self.__plot_update, init_func=self.__plot_init, interval=refresh_interval, blit=True)
            plt.show()
    
    # END INTERNAL CLASS
        
    def create_xy_plot(self, mp_queue, trail_seconds, linestyle):
        """
        Handles instantiating the internal plot
        """
        self.plot = self.XYInternal(mp_queue, trail_seconds, linestyle)
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
        self.process = multiprocessing.Process(target=self.create_xy_plot, args=(self.queue, self.trail_seconds, self.linestyle))
        self.process.start()

    def update(self, x, y):
        """
        Update the live plot with a new data point!
        """
        if not self.is_started:
            raise Exception("Call to update before plot was started. Call XY.start first.")
        if self.trail_seconds != -1:
            # If trail specified, send time of update as well
            self.queue.put((x, y, time.time_ns()))
        else:
            # Else send only data
            self.queue.put((x, y))
    
    def quit(self):
        """
        End the live plotter.
        """
        self.process.terminate()
        self.is_started = False