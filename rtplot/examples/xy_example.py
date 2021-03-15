import rtplot
from rtplot.helpers import random_walk

walker = random_walk()

with rtplot.XY(seconds_to_show=3) as plot:
    while True:
        xy = next(walker)
        plot.update(xy)
