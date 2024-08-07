#! /usr/bin/env python
# encoding: utf-8

from waflib.Build import BuildContext
import os
import sys
import shutil
import hashlib
import subprocess

from waflib.Configure import conf
from waflib import Logs

import waflib

top = "."

VERSION = "2.0.0"


class UploadContext(BuildContext):
    cmd = "upload"
    fun = "upload"


def options(opt):
    opt.add_option(
        "--run_tests", default=False, action="store_true", help="Run all unit tests"
    )

    opt.add_option(
        "--pytest_basetemp",
        default="pytest_temp",
        help="Set the basetemp folder where pytest executes the tests",
    )


def build(bld):
    # Create a virtualenv in the source folder and build universal wheel

    with bld.create_virtualenv() as venv:
        venv.run("python -m pip install wheel")
        venv.run("python setup.py bdist_wheel --universal")

        # Run the unit-tests
        if bld.options.run_tests:
            _pytest(bld=bld, venv=venv)

    # Delete the egg-info directory, do not understand why this is created
    # when we build a wheel. But, it is - perhaps in the future there will
    # be some way to disable its creation.
    egg_info = os.path.join(
        bld.srcnode.abspath(), "src", "pytest_datarecorder.egg-info"
    )

    if os.path.isdir(egg_info):
        waflib.extras.wurf.directory.remove_directory(path=egg_info)


def _find_wheel(ctx):
    """Find the .whl file in the dist folder."""

    wheel = ctx.path.ant_glob("dist/*-" + VERSION + "-*.whl")

    if not len(wheel) == 1:
        ctx.fatal("No wheel found (or version mismatch)")
    else:
        wheel = wheel[0]
        Logs.info("Wheel %s", wheel)
        return wheel


def upload(bld):
    """Upload the built wheel to PyPI (the Python Package Index)"""

    with bld.create_virtualenv() as venv:
        venv.run("python -m pip install twine")

        wheel = _find_wheel(ctx=bld)

        venv.run("python -m twine upload {}".format(wheel))


def prepare_release(ctx):
    """Prepare a release."""

    with ctx.rewrite_file(filename="setup.py") as f:
        pattern = r'VERSION = "\d+\.\d+\.\d+"'
        replacement = f'VERSION = "{VERSION}"'

        f.regex_replace(pattern=pattern, replacement=replacement)


def _pytest(bld, venv):
    # To update the requirements.txt just delete it - a fresh one
    # will be generated from test/requirements.in
    # Ensure that the requirements.txt is up to date
    bld.pip_compile(
        requirements_in="test/requirements.in", requirements_txt="test/requirements.txt"
    )

    venv.run("python -m pip install -r test/requirements.txt")

    # Install the pytest-testdirectory plugin in the virtualenv
    wheel = _find_wheel(ctx=bld)

    venv.run(f"python -m pip install {wheel}")

    # We override the pytest temp folder with the basetemp option,
    # so the test folders will be available at the specified location
    # on all platforms. The default location is the "pytest" local folder.
    basetemp = os.path.abspath(os.path.expanduser(bld.options.pytest_basetemp))

    # We need to manually remove the previously created basetemp folder,
    # because pytest uses os.listdir in the removal process, and that fails
    # if there are any broken symlinks in that folder.
    if os.path.exists(basetemp):
        waflib.extras.wurf.directory.remove_directory(path=basetemp)

    testdir = bld.path.find_node("test")

    # Make python not write any .pyc files. These may linger around
    # in the file system and make some tests pass although their .py
    # counter-part has been e.g. deleted
    venv.run(f"python -B -m pytest {testdir.abspath()} --basetemp {basetemp}")
