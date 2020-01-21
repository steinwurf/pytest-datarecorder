import os
import json
import sys
import io
import pprint
import difflib
import pytest
import tempfile


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

    def record_data(self, src_data, dst_file, mismatch_path=None):
        """ Record and compare data with existing recording.

        :param recording_file: The file path to the recording. The extension
            will determine the type of recorder used.
            Typically recordings are put under version control.
        :param mismatch_path: The directory to where the mismatched
            recording should be stored. E.g. /tmp/mismatch note these should NOT
            be placed under version control.
        """

        if recording_file is None:
            raise RuntimeError("You need to provide a file path for "
                               "the recording.")

        recording_path, filename = os.path.split(recording_file)

        if not os.path.isdir(recording_path):
            raise RuntimeError("The recording directory {}. Is invalid "
                               "or does not exist.".format(recording_path))

        _, extension = os.path.splitext(filename)

        if not extension in extension_map:
            raise NotImplementedError("We have no mapping for {}".format(
                extension))

        if mismatch_path is None:
            mismatch_path = os.path.join(tempfile.gettempdir(), 'datarecorder')

        if recording_path == mismatch_path:
            raise RuntimeError(
                "Recording and mismatch path cannot be ther same.")

        if not os.path.isdir(mismatch_path):
            os.makedirs(mismatch_path)

        # Instantiate the recorder
        recorder_class = extension_map[extension]
        recorder = recorder_class()

        recorder.record_data(
            data=data, filename=filename, recording_path=recording_path,
            mismatch_path=mismatch_path)

    def record_file(self, src_file, dst_file, mismatch_path=None):

        if not os.path.isfile(file_path):
            raise RuntimeError(f"Not a file")


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


def save_recording(dst_file, src_data):

    with io.open(recording_file, 'w', encoding='utf-8') as recording_fp:
        recording_fp.write(recording_data)


def copy_recording(dst_file, src_file):


def has_recording(recording_file):
    return os.path.isfile(recording_file)


def load_recording(src_file):
    with io.open(recording_file, 'r', encoding='utf-8') as recording_fp:
        return recording_fp.read()


class TextDataRecorder(object):

    def __init__(self, mismatch_path):
        """ Create a new instance.

        :param mismatch_path: Location for storing
        """

    def save_recording(self, data, new_file):
        pass

    def has_recording(self, )

    def record_data(self, new_data, old_file):
        """ Record the data

        :param data: Some text to record
        :param recording_file: An existing recording to compare with. If no
            previous recording exists we save our data to file.
        :param mismatch_file: If an existing recording exist we save the data
            to the mismatch file for later inspection.
        """

        # Do we have a recording?
        if not has_recording(recording_file):
            save_recording(recording_file, new_recording_data)
            return

        # A recording exists
        old_recording_data = load_recording(recording_file)

        assert type(new_recording_data) == type(old_recording_data)
        if new_recording_data == old_recording_data:
            return

        # There is a recording mismatch
        mismatch_file = os.path.join(mismatch_path, filename)

        save_recording(mismatch_file, new_recording_data)

        raise DataRecorderError(
            filename=self.filename,
            recording_path=self.recording_path, recording_data=recording_data,
            mismatch_path=self.mismatch_path, mismatch_data=data)

    def record_file(self, new_file, old_file):

        # No recording exist?
        if not has_recording(old_file):

            # Save the recording
            new_data = load_recording(filename=new_file)
            save_recording(filename=old_file, data=new_data)

            return

        # Check for mismatch
        new_data = load_recording(new_file)
        old_data = load_recording(old_file)

        if new_data == old_data:
            return

        raise DataRecorderError(new_data=new_data, old_data=old_data,
                                new_file=new_file, old_file=old_file,
                                mismatch_path=self.mismatch_path)


class JsonDataRecorder(TextDataRecorder):

    def __init__(self, filename, recording_path, mismatch_path):
        super(JsonDataRecorder, self).__init__(
            filename, recording_path, mismatch_path)

    def record(self, data):

        # Convert the data to json
        data = json.dumps(data, indent=2, sort_keys=True,
                          separators=(',', ': '))

        super(JsonDataRecorder, self).record(data=data)


# Extension map for the different output files we support
extension_map = {
    '.json': JsonDataRecorder,
    '.rst': TextDataRecorder,
    '.txt': TextDataRecorder
}
