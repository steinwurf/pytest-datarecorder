import os
import json
import sys
import io
import pprint
import difflib
import pytest
import tempfile
import pathlib


class RecorderOptions:
    def __init__(
        self,
        recording_file,
        mismatch_dir=None,
        recording_type=None,
        mismatch_callback=None,
        mismatch_context=None,
    ):

        self.recording_file = pathlib.Path(recording_file)

        # Check the recording directory exists
        self.recording_dir = self.recording_file.parent
        os.makedirs(self.recording_dir, exist_ok=True)

        # We only lazily create the mismatch directory if needed
        if mismatch_dir is not None:
            self._mismatch_dir = pathlib.Path(mismatch_dir)
        else:
            self._mismatch_dir = mismatch_dir

        # If we have no recording type use the file extension
        if not recording_type:
            # Also drop the '.' in the suffix
            self.recording_type = self.recording_file.suffix[1:]
        else:
            self.recording_type = recording_type

        if not self.recording_type in extension_map:
            raise NotImplementedError(
                f"We have no mapping for recording type {recording_type}"
            )

        self.mismatch_callback = mismatch_callback
        self.mismatch_context = mismatch_context

    @property
    def mismatch_dir(self):
        # If we do not have a mismatch_dir we provide one
        if self._mismatch_dir is None:

            # Create the datarecorder directory
            parent_dir = os.path.join(tempfile.gettempdir(), "datarecorder")
            os.makedirs(parent_dir, exist_ok=True)

            # Create a unique directory
            self._mismatch_dir = pathlib.Path(
                tempfile.mkdtemp(prefix="mismatch_", dir=parent_dir)
            )
        else:
            # Ensure the directory exists
            os.makedirs(self._mismatch_dir, exist_ok=True)

        return self._mismatch_dir

    @property
    def mismatch_file(self):
        return self.mismatch_dir.joinpath(self.recording_file.name)


class DataRecorder(object):
    """The DataRecorder object is a small test helper. Working similarly to
        vcrpy etc.

    You give it a recording path (filename) now when calling record(..)
    the following will happen:

    1. If a "recording" already suggests we check to see if the data
       matches
    2. If no "recording" exists we store it in the file.

    The file can be committed to version control. To accept a change in the
    output just delete the existing recording and make a new one.
    """

    def record_data(
        self,
        data,
        recording_file,
        mismatch_dir=None,
        recording_type=None,
        mismatch_callback=None,
        mismatch_context=None,
    ):
        """Record and compare data with existing recording.

        :param recording_file: The file path to the recording. The extension
            will determine the type of recorder used. Typically recordings are
            put under version control.
        :param mismatch_path: The directory to where the mismatched recording
            should be stored. E.g. /tmp/mismatch note these should NOT be placed
            under version control.
        :param recording_type: The recording type to use. In cases where the
            recording_file does not have an file extension, then the recording
            type can be specified here.
        :param mismatch_callback: A callback function that will be called when
            a mismatch is detected. The callback will be called with the
            following arguments:
                - recording_data as a string (the data that was in the recording)
                - mismatch_data as a string (the data that was recorded)
                - mismatch_dir as a string (store mismatch artifacts here)
                - mismatch_context user provided
            The callback can return a string that will be used in the
            mismatch error message.

        """

        options = RecorderOptions(
            recording_file=recording_file,
            mismatch_dir=mismatch_dir,
            recording_type=recording_type,
            mismatch_callback=mismatch_callback,
            mismatch_context=mismatch_context,
        )

        recorder = extension_map[options.recording_type]["data"]
        recorder(data=data, options=options)

    def record_file(
        self,
        data_file,
        recording_file,
        mismatch_dir=None,
        recording_type=None,
        mismatch_callback=None,
        mismatch_context=None,
    ):
        """Record and compare data with existing recording.

        :param data_file: The input file containing the data to be recorded
        :param recording_file: The file path to the recording. The extension
            will determine the type of recorder used.
            Typically recordings are put under version control.
        :param mismatch_path: The directory to where the mismatched
            recording should be stored. E.g. /tmp/mismatch note these should NOT
            be placed under version control.
        :param recording_type: The recording type to use. In cases where the
            recording_file does not have an file extension, then the recording
            type can be specified here.
        :param mismatch_callback: A callback function that will be called when
            a mismatch is detected. The callback will be called with the
            following arguments:
                - recording_data as a string (the data that was in the recording)
                - mismatch_data as a string (the data that was recorded)
                - mismatch_dir as a string (store mismatch artifacts here)
                - mismatch_context user provided
            The callback can return a string that will be used in the
            mismatch error message.

        """
        options = RecorderOptions(
            recording_file=recording_file,
            mismatch_dir=mismatch_dir,
            recording_type=recording_type,
            mismatch_callback=mismatch_callback,
            mismatch_context=mismatch_context,
        )

        recorder = extension_map[options.recording_type]["file"]
        recorder(data_file=data_file, options=options)


class DataRecorderError(Exception):
    """Basic exception for errors raised when running commands."""

    def __init__(
        self,
        mismatch_file,
        recording_file,
        user_error,
    ):

        error = (
            f"Data mismatch between {recording_file} and {mismatch_file}\n"
            f"User error: {user_error}\n"
        )

        super(DataRecorderError, self).__init__(error)


def record_data_text(data, options):
    """Record the data

    :param data: Some text to record
    """

    # No recording exist?
    if not options.recording_file.is_file():
        # Save the recording
        with io.open(options.recording_file, "w", encoding="utf-8") as text_file:
            text_file.write(data)

        return

    # Check for mismatch
    with io.open(options.recording_file, "r", encoding="utf-8") as text_file:
        recording_data = text_file.read()

    if data == recording_data:
        return

    with io.open(options.mismatch_file, "w", encoding="utf-8") as text_file:
        text_file.write(data)

    # Call the mismatch callback
    if options.mismatch_callback:
        user_error = options.mismatch_callback(
            mismatch_data=data,
            recording_data=recording_data,
            mismatch_dir=options.mismatch_dir,
            mismatch_context=options.mismatch_context,
        )
    else:
        user_error = None

    raise DataRecorderError(
        mismatch_file=options.mismatch_file,
        recording_file=options.recording_file,
        user_error=user_error,
    )


def record_file_text(data_file, options):
    """Check the file content."""

    with io.open(data_file, "r", encoding="utf-8") as text_file:
        data = text_file.read()

    record_data_text(
        data=data,
        options=options,
    )


def record_data_json(data, options):
    def default(data):
        """The JSON module will call this function for types it does
        not know. We just convert to string an pray it works :)
        """
        return str(data)

    # Convert the data to json
    data = json.dumps(
        data, indent=2, sort_keys=True, separators=(",", ": "), default=default
    )

    record_data_text(data=data, options=options)


# Extension map for the different output files we support
extension_map = {
    "json": {"file": record_file_text, "data": record_data_json},
    "rst": {"file": record_file_text, "data": record_data_text},
    "txt": {"file": record_file_text, "data": record_data_text},
    "html": {"file": record_file_text, "data": record_data_text},
}
