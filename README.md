# rtplot

_Author: Nabeel Sherazi, sherazi.n@husky.neu.edu_


Have you ever noticed how if you want to plot a data stream in real time using matplotlib, it's uhhhhhh absolutely impossible? Like something about FuncAnimation and threading and basically all of this stuff -- IT'S SO FRICKING HARD TO JUST PLOT A DATA STREAM IN REAL TIME.

Well I Googled about this for like six hours and found literally not a single library that would just let me looking at a frickin stream of numbers in real time. So I said okay fine I'll just frickin write it myself and then put it out there so no one ever has to struggle with this again.

## Presenting: rtplot --  it's real time plotting, but it's actually easy!!! For once!!!

Literally just import it. Start a plot. Push data to the plot whenever you want. Or don't. It literally doesn't matter. rtplot can do real-time XY plots and real time timeseries (single variable) data. It's so sweet.

## Usage

Look at this.

```lang=py
from rtplot import TimeSeries

plot = TimeSeries(seconds_to_show=10)

plot.start()

while True:
    new_data = read_sensor_data()
    plot.update(new_data)

plot.quit()

```

BRUH!!!!!

```lang=py
from rtplot import XY

plot = XY(trail_seconds=3) # Or not! Leave blank to show all data

plot.start()

while True:
    (x, y) = next(random_walk)
    plot.update(x, y)

plot.quit()

```

Supports context managers too

```lang=py

with rtplot.XY() as plot:
    (x, y) = datastream.read()
    plot.update(x, y)

```

## Install

Either download this repo or just run `pip install rtplot`

Natively Python 3 unlike some of the solutions I found!!!! Only dependencies numpy and matplotlib.

