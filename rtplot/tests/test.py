from rtplot import TimeSeries, XY
import rtplot.shortcuts.line
import time
import numpy as np
import math
from rtplot.examples.rand_data_generators import random_walk, random_timeseries, sinusoid


if __name__ == "__main__":

    generators = []
    for i in range(2):
        generators.append(random_timeseries())
    
    start = time.time()

    plot = TimeSeries(10, linestyle=["r-", "b-"])
    plot.add_static("vline", x=5, **rtplot.shortcuts.line.red_line)

    plot.start()

    start_time = time.time()
    while time.time() - start_time < 30:
        try:
            data = [next(walker) for walker in generators]
            plot.update(data)
            time.sleep(.1)
        except KeyboardInterrupt:
            break

    plot.quit()