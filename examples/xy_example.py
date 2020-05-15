from rand_data_generators import random_walk
import rtplot

walker = random_walk()

with rtplot.XY(seconds_to_show=3) as plot:
    while True:
        xy = next(walker)
        plot.update(xy)