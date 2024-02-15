News for pytest-datarecorder
============================

This file lists the major changes between versions. For a more detailed list
of every change, see the Git log.

Latest
------
* tbd

1.7.0
-----
* Minor: Added more context to the DataRecorderError exception.

1.6.0
-----
* Minor: Added access to the user_error on the exception object

1.5.0
-----
* Minor: Adding mismatch_context parameter. This allows users to use the
  same mismatch callback for multiple data recorders. The context can be used
  to differentiate between the different data recorders. The context is
  passed to the mismatch callback function and can contain any data.

1.4.0
-----
* Minor: Adding support for mismatch callback functions. The will allow custom
  handling of mismatched data.

1.3.0
-----
* Minor: Added support for passing a recording_type to the data recorder. This
  makes it possible to record into files / data that do not have a files
  extension.

1.2.0
-----
* Minor: For JSON recording support custom types like pathlib.Path objects.

1.1.0
-----
* Minor: Added support for ``html`` files.

1.0.1
-----
* Patch: Fix syntax in README.rst for upload to pypi.

1.0.0
-----
* Major: Updated API and support for recording files in addition
  to data objects.
* Major: Initial release
