import rtplot
from rtplot.helpers import random_timeseries

generator = random_timeseries()

if __name__ == "__main__":
    with rtplot.TimeSeries(seconds_to_show=10, timeout=10) as plot:
        while True:
            next_pt = next(generator)
            plot.update(next_pt)
