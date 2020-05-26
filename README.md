# rtplot

_Author: Nabeel Sherazi, sherazi.n@husky.neu.edu_

Have you ever noticed how if you want to plot a data stream in real time using matplotlib, it's uhhhhhh absolutely impossible? Like something about FuncAnimation and threading and basically all of this stuff -- IT'S SO FRICKING HARD TO JUST PLOT A DATA STREAM IN REAL TIME.

Well I Googled about this for like six hours and found literally not a single library that would just let me looking at a frickin stream of numbers in real time. So I said okay fine I'll just frickin write it myself and then put it out there so no one ever has to struggle with this again.

## Presenting: rtplot -- it's real time plotting, but it's actually easy!!! For once!!!

Literally just import it. Start a plot. Push data to the plot whenever you want. Or don't. It literally doesn't matter. rtplot can do real-time XY plots, 3D plots, and timeseries (single variable) data. It's so sweet. It can do multiple plots too. Like 20 timeseries at once. At 60 fps. Seriously.

## Usage

Look at this.

```python
from rtplot import TimeSeries

plot = TimeSeries(seconds_to_show=10)

plot.start()

while True:
    new_data = read_sensor_data()
    plot.update(new_data)

plot.quit()

```

BRUH!!!!!

```python
from rtplot import XY

plot = XY(seconds_to_show=3) # Or not! Leave blank to show all data

plot.start()

while True:
    xy1 = robot1.position()
    xy2 = robot2.position()
    plot.update([xy1, xy2])

plot.quit()

```

oh you thought i was JOKING?????

```python
from rtplot import Z3D

plot = Z3D(seconds_to_show=1)

plot.start()

while True:
    xy = drone.gps_position()
    z = drone.altitude()
    plot.update([*xy, z])

plot.quit()

```

Supports context managers, custom linestyles, static background drawings, shortcuts, and more too!!! It's so fricking BATTERIES INCLUDED.

```python

# Context manager
with rtplot.XY() as plot:
    xy = datastream.read()
    plot.update(x, y)

# Statics
plot1 = rtplot.TimeSeries(seconds_to_show=10, linestyle='r-')
plot1.add_static("vline", x=5)

# Shortcuts for common linestyles
import rtplot.shortcuts.shape as shape_shortcuts
plot1.add_static("rectangle", **shape_shortcuts.blue_dotted_stroke)

# By the way, this is safe since EVERY PLOT IS IN ITS OWN THREAD!!!

plot1.start()
plot2 = rtplot.XY(seconds_to_show=10, linestyle=["r-", "b:"]) # Let rtplot know in advance there should be two lines
plot2.start()

```

Basically this stuff goes off man.

## Install

Either download this repo or just run `pip install rtplot`

Natively Python 3 unlike some of the solutions I found!!!! Only external dependencies numpy and matplotlib.
One day I'll write some real docs for this but for now the source code is really small so if you don't get how to use something just look at the source code. I think I commented it pretty well. Also see the examples.

DEUCES
