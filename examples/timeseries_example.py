from rand_data_generators import random_timeseries
import rtplot

generator = random_timeseries()

with rtplot.TimeSeries(seconds_to_show=10) as plot:
    while True:
        next_pt = next(generator)
        plot.update(next_pt)