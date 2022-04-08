from typing import Iterable, Tuple
import numpy as np
import random

def random_2d_bounce(x_bound: float = 10.0, y_bound: float = 10.0) -> Tuple(float):
    """Generates data that walks between +/- (x_bound, y_bound)"""
    rnd = random.Random()
    x = 0.00
    y = 0.00
    vx = 0.5 + rnd.random() / 2
    vy = 0.5 + rnd.random() / 2
    while True:
        if abs(x) >= x_bound:
            vx = -vx
        if abs(y) >= y_bound:
            vy = -vy

        if rnd.random() > 0.9:
            if rnd.random() >= 0.5:
                vx = np.sign(vx) * (0.5 + rnd.random() / 2)
            else:
                vy = np.sign(vy) * (0.5 + rnd.random() / 2)

        x += vx
        y += vy
        yield (x, y)


def random_1d_walk(initial_x: float = 5) -> float:
    """Generates data that starts at initial_x and walks randomly up or down"""
    x = initial_x
    rnd = random.Random()

    while True:
        if rnd.random() > 0.5:
            x += 0.1 * rnd.random()
        else:
            x -= 0.1 * rnd.random()
        yield x


def sinusoid(A: float = 1, omega: float = 2*np.pi) -> float:
    """Generates data corresponding to a sinusoid with amplitude A and angular frequency omega (in rads)"""
    phi = 0.00
    while True:
        phi += 0.01
        yield A * float(np.sin(omega * phi))