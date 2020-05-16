from rtplot import TimeSeries, XY
import rtplot.shortcuts.line
from rtplot.examples.rand_data_generators import random_walk, random_timeseries, sinusoid
import time
from contextlib import suppress

if __name__ == "__main__":
    generators = []
    for i in range(2):
        generators.append(random_timeseries())

    start = time.time()

    plot = TimeSeries(10, linestyle=["r-", "b-"])
    plot.add_static("vline", x=5, **rtplot.shortcuts.line.red_line)

    plot.start()

    start_time = time.time()
    with suppress(KeyboardInterrupt):
        while time.time() - start_time < 30:
            data = [next(walker) for walker in generators]
            plot.update(data)
            time.sleep(.1)
    plot.quit()