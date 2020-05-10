from rand_data_generators import random_timeseries
import liveplot

generator = random_timeseries()

with liveplot.TimeSeries(seconds_to_show=10) as plot:
    while True:
        next_pt = next(generator)
        plot.update(next_pt)