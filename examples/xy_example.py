from rand_data_generators import random_walk
import liveplot

walker = random_walk()

with liveplot.XY(trail_seconds=3) as plot:
    while True:
        (x, y) = next(walker)
        plot.update(x, y)