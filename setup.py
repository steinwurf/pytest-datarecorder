import os
import io
import re
import sys

from setuptools import setup, find_packages

cwd = os.path.abspath(os.path.dirname(__file__))

with io.open(os.path.join(cwd, "README.rst"), encoding="utf-8") as fd:
    long_description = fd.read()

VERSION = "1.3.0"

setup(
    name="pytest-datarecorder",
    version=VERSION,
    description=("A py.test plugin recording and comparing test output."),
    long_description=long_description,
    long_description_content_type="text/x-rst",
    url="https://github.com/steinwurf/pytest-datarecorder",
    author="Steinwurf ApS",
    author_email="contact@steinwurf.com",
    license='BSD 3-clause "New" or "Revised" License',
    classifiers=[
        "Framework :: Pytest",
        "Development Status :: 5 - Production/Stable",
        "Environment :: Plugins",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
        "Topic :: Software Development",
        "Topic :: Software Development :: Testing",
    ],
    keywords=("pytest py.test " "testing unit tests plugin"),
    packages=find_packages(where="src", exclude=["test"]),
    package_dir={"": "src"},
    install_requires=["pytest"],
    entry_points={
        "pytest11": ["datarecorder = pytest_datarecorder.fixtures"],
    },
)
