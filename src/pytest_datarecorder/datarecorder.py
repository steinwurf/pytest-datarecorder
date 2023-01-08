import os
import json
import sys
import io
import pprint
import difflib
import pytest
import tempfile
import pathlib


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
            The callback can return a string that will be used in the
            mismatch error message.

        """
        # Convert to pathlib objects
        recording_file = pathlib.Path(recording_file)
        mismatch_dir = self._prepare_mismatch_dir(mismatch_dir)

        # Instantiate the recorder
        recorder = self._prepare_recording(
            recording_file=recording_file,
            mismatch_dir=mismatch_dir,
            recording_type=recording_type,
        )

        recorder.record_data(
            data=data,
            recording_file=recording_file,
            mismatch_dir=mismatch_dir,
            mismatch_callback=mismatch_callback,
        )

    def record_file(
        self,
        data_file,
        recording_file,
        mismatch_dir=None,
        recording_type=None,
        mismatch_callback=None,
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
            The callback can return a string that will be used in the
            mismatch error message.

        """
        # Convert to pathlib objects
        data_file = pathlib.Path(data_file)
        recording_file = pathlib.Path(recording_file)
        mismatch_dir = self._prepare_mismatch_dir(mismatch_dir)

        # The data file must exist
        if not data_file.is_file():
            raise RuntimeError(f"The data file {data_file} must exists.")

        # Instantiate the recorder
        recorder = self._prepare_recording(
            recording_file=recording_file,
            mismatch_dir=mismatch_dir,
            recording_type=recording_type,
        )

        # Record the file
        recorder.record_file(
            data_file=data_file,
            recording_file=recording_file,
            mismatch_dir=mismatch_dir,
            mismatch_callback=mismatch_callback,
        )

    def _prepare_mismatch_dir(self, mismatch_dir):

        # If we do not have a mismatch_dir we provide one
        if mismatch_dir is None:
            mismatch_dir = os.path.join(tempfile.gettempdir(), "datarecorder")

        mismatch_dir = pathlib.Path(mismatch_dir)

        # If it does not exist we make it
        if not mismatch_dir.is_dir():
            os.makedirs(mismatch_dir)

        return mismatch_dir

    def _prepare_recording(self, recording_file, mismatch_dir, recording_type):
        """Build the handler for this type of recording."""

        # Lets look at the recording_file
        recording_dir = recording_file.parent

        # The mismatch_dir and recording_dir cannot be the same
        if recording_dir == mismatch_dir:
            raise RuntimeError(
                f"Recording and mismatch directory cannot be the same. "
                "was {recording_dir} and {mismatch_dir}"
            )

        # If we have no recording type use the file extension
        if not recording_type:
            # Also drop the '.' in the suffix
            recording_type = recording_file.suffix[1:]

        # Build the actual recorder
        if not recording_type in extension_map:
            raise NotImplementedError(
                "We have no mapping for {}".format(recording_type)
            )

        recorder_class = extension_map[recording_type]
        return recorder_class()


class DataRecorderError(Exception):
    """Basic exception for errors raised when running commands."""

    def __init__(
        self,
        mismatch_data,
        mismatch_file,
        recording_data,
        recording_file,
        mismatch_dir,
        user_error,
    ):

        # Unified diff expects a list of strings
        recording_lines = recording_data.split("\n")
        mismatch_lines = mismatch_data.split("\n")

        diff = difflib.unified_diff(
            a=recording_lines,
            b=mismatch_lines,
            fromfile=str(recording_file),
            tofile=str(mismatch_file),
        )

        # Unified_diff(...) returns a generator so we need to force the
        # data by interation - and then convert back to one string
        diff = "\n".join(list(diff))

        # Some differences are not easy to see with the unified diff console
        # output e.g. trailing white-spaces etc. So we also dump a HTML diff
        # output
        html_diff = difflib.HtmlDiff().make_file(
            fromlines=recording_lines,
            tolines=mismatch_lines,
            fromdesc=recording_file,
            todesc=mismatch_file,
        )
        html_file = mismatch_dir.joinpath("diff.html")

        with io.open(html_file, "w", encoding="utf-8") as html_fp:
            html_fp.write(html_diff)

        result = "Diff:\n{}\nHTML diff:\n{}\n".format(diff, html_file)

        if user_error:
            result += f"{user_error}\n"

        super(DataRecorderError, self).__init__(result)


class TextDataRecorder(object):
    def record_data(self, data, recording_file, mismatch_dir, mismatch_callback):
        """Record the data

        :param data: Some text to record
        :param recording_file: An existing recording to compare with. If no
            previous recording exists we save our data to file.
        :param mismatch_file: If an existing recording exist we save the data
            to the mismatch file for later inspection.
        :param mismatch_callback: A callback function that will be called when
            a mismatch is detected.
        """

        # No recording exist?
        if not recording_file.is_file():

            # Save the recording
            with io.open(recording_file, "w", encoding="utf-8") as text_file:
                text_file.write(data)

            return

        # Check for mismatch
        with io.open(recording_file, "r", encoding="utf-8") as text_file:
            recording_data = text_file.read()

        if data == recording_data:
            return

        # We have a mismatch

        # Save the new data in the mismatch path
        mismatch_file = mismatch_dir.joinpath(recording_file.name)

        with io.open(mismatch_file, "w", encoding="utf-8") as text_file:
            text_file.write(data)

        # Call the mismatch callback
        if mismatch_callback:
            user_error = mismatch_callback(
                mismatch_data=data,
                recording_data=recording_data,
                mismatch_dir=mismatch_dir,
            )
        else:
            user_error = None

        raise DataRecorderError(
            mismatch_data=data,
            mismatch_file=mismatch_file,
            recording_data=recording_data,
            recording_file=recording_file,
            mismatch_dir=mismatch_dir,
            user_error=user_error,
        )

    def record_file(self, data_file, recording_file, mismatch_dir, mismatch_callback):
        """Check the file content."""

        with io.open(data_file, "r", encoding="utf-8") as text_file:
            data = text_file.read()

        self.record_data(
            data=data,
            recording_file=recording_file,
            mismatch_dir=mismatch_dir,
            mismatch_callback=mismatch_callback,
        )


class JsonDataRecorder(object):
    def __init__(self):
        self.text_recorder = TextDataRecorder()

    def record_data(self, data, recording_file, mismatch_dir, mismatch_callback):
        def default(data):
            """The JSON module will call this function for types it does
            not know. We just convert to string an pray it works :)
            """
            return str(data)

        # Convert the data to json
        data = json.dumps(
            data, indent=2, sort_keys=True, separators=(",", ": "), default=default
        )

        self.text_recorder.record_data(
            data=data,
            recording_file=recording_file,
            mismatch_dir=mismatch_dir,
            mismatch_callback=mismatch_callback,
        )

    def record_file(self, data_file, recording_file, mismatch_dir, mismatch_callback):

        self.text_recorder.record_file(
            data_file=data_file,
            recording_file=recording_file,
            mismatch_dir=mismatch_dir,
            mismatch_callback=mismatch_callback,
        )


# Extension map for the different output files we support
extension_map = {
    "json": JsonDataRecorder,
    "rst": TextDataRecorder,
    "txt": TextDataRecorder,
    "html": TextDataRecorder,
}
