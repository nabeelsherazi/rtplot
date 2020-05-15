import setuptools
from core import __version__

with open("README.md", "r") as fh:
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
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 3 - Alpha",
        "Framework :: Matplotlib",
        "Intended Audience :: Science/Research"
    ],
    python_requires='>=3.6',
)