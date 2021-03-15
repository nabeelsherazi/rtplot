from rtplot import TimeSeries
import rtplot.shortcuts.line
from rtplot.helpers import random_timeseries, Timer
import time


def test_statics():
    if __name__ == "tests.test_timeseries":
        generators = []
        for i in range(2):
            generators.append(random_timeseries())

        plot = TimeSeries(seconds_to_show=3, linestyle=["r-", "b-"])
        plot.add_static("vline", x=5, **rtplot.shortcuts.line.red_line)

        plot.start()
        timer = Timer(5)

        while not timer.done:
            data = [next(walker) for walker in generators]
            plot.update(data)
            time.sleep(.1)
        plot.quit()


def test_context_manager():
    if __name__ == "tests.test_timeseries":
        generators = []
        for i in range(2):
            generators.append(random_timeseries())

        timer = Timer(5)
        while not timer.done:
            with TimeSeries(time_to_show=3) as plot:
                data = [next(walker) for walker in generators]
                plot.update(data)
                time.sleep(.1)
