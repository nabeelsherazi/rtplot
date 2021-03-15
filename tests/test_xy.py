import pytest
from rtplot import XY
import rtplot.shortcuts.line
from rtplot.helpers import random_walk, Timer
import time


@pytest.fixture(autouse=True)
def check_name():
    if not __name__.startswith("tests"):
        assert False


@pytest.fixture
def two_walkers():
    generators = []
    for i in range(2):
        generators.append(random_walk())
    return generators


def test_statics(check_name, two_walkers):

    plot = XY(seconds_to_show=3, linestyle=["r-", "b-"])
    plot.add_static("vline", x=5, **rtplot.shortcuts.line.red_line)

    plot.start()
    timer = Timer(5)

    while not timer.done:
        data = [next(walker) for walker in two_walkers]
        plot.update(data)
        time.sleep(.1)
    plot.quit()


def test_context_manager(check_name, two_walkers):

    timer = Timer(5)
    while not timer.done:
        with XY(seconds_to_show=3) as plot:
            data = [next(walker) for walker in two_walkers]
            plot.update(data)
            time.sleep(.1)
