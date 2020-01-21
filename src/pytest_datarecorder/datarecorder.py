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
    """ The DataRecorder object is a small test helper. Working similarly to
        vcrpy etc.

    You give it a recording path (filename) now when calling record(..)
    the following will happen:

    1. If a "recording" already suggests we check to see if the data
       matches
    2. If no "recording" exists we store it in the file.

    The file can be committed to version control. To accept a change in the
    output just delete the existing recording and make a new one.
    """

    def record_data(self, data, recording_file, mismatch_dir=None):
        """ Record and compare data with existing recording.

        :param recording_file: The file path to the recording. The extension
            will determine the type of recorder used.
            Typically recordings are put under version control.
        :param mismatch_path: The directory to where the mismatched
            recording should be stored. E.g. /tmp/mismatch note these should NOT
            be placed under version control.
        """
        # Instantiate the recorder
        recorder = self._prepare_recording(
            recording_file=recording_file, mismatch_dir=mismatch_dir)

        recorder.record_data(
            data=data, recording_file=recording_file, mismatch_dir=mismatch_dir)

    def record_file(self, data_file, recording_file, mismatch_dir=None):

        # Convert to pathlib objects
        data_file = pathlib.Path(data_file)
        recording_file = pathlib.Path(recording_file)

        if data_file.suffix != recording_file.suffix:
            raise RuntimeError(f'Invalid file format for file {data_file.suffix} '
                               'and recording {recording_file.suffix}')

        # Instantiate the recorder
        recorder = self._prepare_recording(
            recording_file=recording_file, mismatch_dir=mismatch_dir)

        # Record the file
        recorder.record_file(
            data_file=data_file, recording_file=recording_file,
            mismatch_dir=mismatch_dir)

    def _prepare_recording(self, recording_file, mismatch_dir):
        """ Build the handler for this type of recording. """

        # If we do not have a mismatch_dir we provide one
        if mismatch_dir is None:
            mismatch_dir = pathlib.Path(
                tempfile.gettempdir()).joinpath('datarecorder')

        # If it does not exist we make it
        if not mismatch_dir.is_dir():
            os.makedirs(mismatch_dir)

        # Lets look at the recording_file
        recording_file = pathlib.Path(recording_file)
        recording_dir = recording_file.parent

        # The mismatch_dir and recording_dir cannot be the same
        if recording_dir == mismatch_dir:
            raise RuntimeError(
                f'Recording and mismatch directory cannot be the same. '
                'was {recording_dir} and {mismatch_dir}')

        # Build the actual recorder
        if not recording_file.suffix in extension_map:
            raise NotImplementedError("We have no mapping for {}".format(
                recording_file.suffix))

        recorder_class = extension_map[recording_file.suffix]
        return recorder_class()


class DataRecorderError(Exception):
    """Basic exception for errors raised when running commands."""

    def __init__(self, filename, recording_path, mismatch_file,
                 mismatch_data):

        recording_file = os.path.join(recording_path, filename)
        mismatch_file = os.path.join(mismatch_path, filename)

        # Unified diff expects a list of strings
        recording_lines = recording_data.split('\n')
        mismatch_lines = mismatch_data.split('\n')

        diff = difflib.unified_diff(
            a=recording_lines,
            b=mismatch_lines,
            fromfile=recording_file,
            tofile=mismatch_file)

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
            todesc=mismatch_file)
        html_file = os.path.join(mismatch_path, 'diff.html')

        with io.open(html_file, 'w', encoding='utf-8') as html_fp:
            html_fp.write(html_diff)

        result = "Diff:\n{}\nHTML diff:\n{}".format(diff, html_file)
        super(DataRecorderError, self).__init__(result)


def save_recording(filepath, data):
    with io.open(filepath, 'w', encoding='utf-8') as recording_fp:
        recording_fp.write(data)


def has_recording(filepath):
    return os.path.isfile(filepath)


def load_recording(filepath):
    with io.open(filepath, 'r', encoding='utf-8') as recording_fp:
        return recording_fp.read()


def filename_recording(filepath):
    _, filename = os.path.split(filepath)
    return filename


def validate_recording(filepath):

    filepath = pathlib.Path(filepath)


class BaseDataRecorder(object):

    def __init__(self):


class TextDataRecorder(object):

    def __init__(self, mismatch_path):
        """ Create a new instance.

        :param mismatch_path: Location for storing
        """
        self.mismatch_path = mismatch_path

    def serialize_data(self, data):
        return str(data)

    def record_data(self, new_data, old_filepath):
        """ Record the data

        :param data: Some text to record
        :param recording_file: An existing recording to compare with. If no
            previous recording exists we save our data to file.
        :param mismatch_file: If an existing recording exist we save the data
            to the mismatch file for later inspection.
        """

        # No recording exist?
        if not has_recording(filepath=old_filepath):

            # Save the recording
            save_recording(filepath=old_filepath, data=new_data)

            return

        # Check for mismatch
        old_data = load_recording(filepath=old_filepath)

        if new_data == old_data:
            return

        # Save the new data in the mismatch path
        new_filepath = os.path.join(
            self.mismatch_path, filename_recording(filepath=old_filepath))

        save_recording(filepath=new_filepath, data=new_data)

        raise DataRecorderError(
            new_data=new_data, old_data=old_data,
            new_filepath=new_filepath, old_filepath=old_filepath,
            mismatch_path=self.mismatch_path)

    def record_file(self, new_filepath, old_filepath):

        # No recording exist?
        if not has_recording(old_filepath):

            # Save the recording
            new_data = load_recording(filepath=new_filepath)
            save_recording(filepath=old_filepath, data=new_data)

            return

        # Check for mismatch
        new_data = load_recording(filepath=new_filepath)
        old_data = load_recording(filepath=old_filepath)

        if new_data == old_data:
            return

        raise DataRecorderError(new_data=new_data, old_data=old_data,
                                new_filepath=new_filepath, old_filepath=old_filepath,
                                mismatch_path=self.mismatch_path)


class JsonDataRecorder(TextDataRecorder):

    def __init__(self, filename, recording_path, mismatch_path):
        super(JsonDataRecorder, self).__init__(
            filename, recording_path, mismatch_path)

    def serialize_data(self, data):
        # Convert the data to json
        return json.dumps(data, indent=2, sort_keys=True,
                          separators=(',', ': '))


# Extension map for the different output files we support
extension_map = {
    '.json': JsonDataRecorder,
    '.rst': TextDataRecorder,
    '.txt': TextDataRecorder
}
