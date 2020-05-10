import random
import numpy as np

def random_walk(bounds=(10, 10)):
    """ Bounces around """
    rnd = random.Random()
    xbound = bounds[0]
    ybound = bounds[1]
    x = 0.00
    y = 0.00
    vx = 0.5 + rnd.random() / 2
    vy = 0.5 + rnd.random() / 2
    while True:
        if abs(x) >= xbound:
            vx = -vx
        if abs(y) >= ybound:
            vy = -vy
        
        if rnd.random() > 0.9:
            if rnd.random() >= 0.5:
                vx = np.sign(vx) * (0.5 + rnd.random() / 2)
            else:
                vy = np.sign(vy) * (0.5 + rnd.random() / 2)

        x += vx
        y += vy
        yield (x, y)

def random_timeseries():
    y = 5
    rnd = random.Random()

    while True:
        if rnd.random() > 0.5:
            y += 0.1 * rnd.random()
        else:
            y -= 0.1 * rnd.random()
        yield y

def sinusoid(A, omega):
    phi = 0.00
    while True:
        phi += 0.01
        yield A * float(np.sin(omega * phi))

