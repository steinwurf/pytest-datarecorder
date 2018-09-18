import pytest_datarecorder
import os
import pytest


def test_record_json(testdirectory, datarecorder):

    recording_path = testdirectory.mkdir('recording')

    datarecorder.recording_path = os.path.join(
        recording_path.path(), "test.json")

    datarecorder.record(data={'foo': 2, 'bar': 3})

    # Calling again with same data should be fine
    datarecorder.record(data={'foo': 2, 'bar': 3})
    datarecorder.record(data={'bar': 3, 'foo': 2})

    # With new data should raise
    with pytest.raises(pytest_datarecorder.datarecorder.DataRecorderError):
        datarecorder.record(data={'foo': 3, 'bar': 3})


def test_record_rst(testdirectory, datarecorder):

    recording_path = testdirectory.mkdir('recording')

    datarecorder.recording_path = os.path.join(
        recording_path.path(), "test.rst")

    datarecorder.record(data="Hello\n=====\nWorld")

    # Calling again with same data should be fine
    datarecorder.record(data="Hello\n=====\nWorld")

    # With new data should raise
    with pytest.raises(pytest_datarecorder.datarecorder.DataRecorderError):
        datarecorder.record(data="Hello\n=====\nwurfapi")


def test_record_no_mapping(testdirectory, datarecorder):

    recording_path = testdirectory.mkdir('recording')

    datarecorder.recording_path = os.path.join(
        recording_path.path(), 'test.tar.gz')

    with pytest.raises(NotImplementedError):

        datarecorder.record(data="{'foo': 2, 'bar': 3}")
