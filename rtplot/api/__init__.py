from .api.TimeSeries import TimeSeries
from .api.XY import XY
from .api.Z3D import Z3D

try:
    TimeSeries
    print("Found available plot: TimeSeries")
except NameError:
    print("Error in importing TimeSeries")

try:
    XY
    print("Found available plot: XY")
except NameError:
    print("Error in importing XY")

try:
    Z3D
    print("Found available plot: Z3D")
except NameError:
    print("Error in importing Z3D")
