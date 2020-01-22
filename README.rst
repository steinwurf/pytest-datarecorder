===================
pytest-datarecorder
===================

.. image:: https://travis-ci.org/steinwurf/pytest-datarecorder.svg?branch=master
    :target: https://travis-ci.org/steinwurf/pytest-datarecorder

Testing code that generates output can be tedious to maintain
 ``pytest-datarecorder`` aims to simplify this task.

.. contents:: Table of Contents:
   :local:

Installation
===========

To install pytest-datarecorder::

    pip install pytest-datarecorder

Usage
=====

To make it easy to use in with py.test the DataRecorder object can be
injected into a test function by using the datarecorder fixture.

Example::

    def test_this_function(datarecorder):

        datarecorder.record_data(
            data={'a':1, 'b':2}, recording_file="test/data/recording.json")

The ``data`` passed will be serialized to JSON since the recording file
has a ``.json`` extension. If ``data`` changes, we will get an exception
containing a diff with what changed. If we want to accept the changes
we simply delete the recording and run the code again.

Relase new version
==================

1. Edit NEWS.rst and wscript (set correct VERSION)
2. Run ::

    ./waf upload

Source code
===========

The main functionality is found in ``src/datarecorder.py`` and the
corresponding unit test is in ``test/test_datarecorder.py`` if you
want to play/modify/fix the code this would, in most cases, be the place
to start.

Developer Notes
===============

We try to make our projects as independent as possible of a local system setup.
For example with our native code (C/C++) we compile as much as possible from
source, since this makes us independent of what is currently installed
(libraries etc.) on a specific machine.

To "fetch" sources we use Waf (https://waf.io/) augmented with dependency
resolution capabilities: https://github.com/steinwurf/waf

The goal is to enable a work-flow where running::

    ./waf configure
    ./waf build --run_tests

Configures, builds and runs any available tests for a given project, such that
you as a developer can start hacking at the code.

For Python project this is a bit unconventional, but we think it works well.

Tests
=====

The tests will run automatically by passing ``--run_tests`` to waf::

    ./waf --run_tests

This follows what seems to be "best practice" advise, namely to install the
package in editable mode in a virtualenv.

Notes
=====

* Why use an ``src`` folder (https://hynek.me/articles/testing-packaging/).
  tl;dr you should run your tests in the same environment as your users would
  run your code. So by placing the source files in a non-importable folder you
  avoid accidentally having access to resources not added to the Python
  package your users will install...
* Python packaging guide: https://packaging.python.org/distributing/
