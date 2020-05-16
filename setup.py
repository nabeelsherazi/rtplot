import setuptools
import shutil
from rtplot.core.version import __version__

print(f"Building rtplot version {__version__}")

print("Cleaning old builds")

shutil.rmtree("./build/", ignore_errors=True)
shutil.rmtree("./dist/", ignore_errors=True)
shutil.rmtree("./rtplot.egg-info/", ignore_errors=True)

with open("./rtplot/README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="rtplot",
    version=__version__,
    author="Nabeel Sherazi",
    author_email="sherazi.n@husky.neu.edu",
    description="Real time plotting. Yes, you can do it now.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/nabeelsherazi/rtplot",
    packages=["rtplot", "rtplot.core", "rtplot.shortcuts", "rtplot.examples"],
    package_data={"": ["LICENSE", "README.md"]},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 3 - Alpha",
        "Framework :: Matplotlib",
        "Intended Audience :: Science/Research"
    ],
    python_requires='>=3.6',
    install_requires=["matplotlib==3.1.3", "numpy>=1.18.1"],
)