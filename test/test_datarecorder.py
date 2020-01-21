import pytest_datarecorder
import os
import pytest


def test_record_json(testdirectory, datarecorder):

    recording_path = testdirectory.mkdir('recording')
    recording_file = os.path.join(recording_path.path(), "test.json")

    datarecorder.record_data(
        data={'foo': 2, 'bar': 3}, recording_file=recording_file)

    # Calling again with same data should be fine
    datarecorder.record_data(
        data={'foo': 2, 'bar': 3}, recording_file=recording_file)

    datarecorder.record_data(
        data={'bar': 3, 'foo': 2}, recording_file=recording_file)

    # With new data should raise
    with pytest.raises(pytest_datarecorder.datarecorder.DataRecorderError):
        datarecorder.record_data(
            data={'foo': 3, 'bar': 3}, recording_file=recording_file)


def test_record_rst(testdirectory, datarecorder):

    recording_path = testdirectory.mkdir('recording')
    recording_file = os.path.join(
        recording_path.path(), "test.rst")

    datarecorder.record_data(data="Hello\n=====\nWorld",
                             recording_file=recording_file)

    # Calling again with same data should be fine
    datarecorder.record_data(data="Hello\n=====\nWorld",
                             recording_file=recording_file)

    # With new data should raise
    with pytest.raises(pytest_datarecorder.datarecorder.DataRecorderError):
        datarecorder.record_data(
            data="Hello\n=====\nwurfapi", recording_file=recording_file)


def test_record_no_mapping(testdirectory, datarecorder):

    recording_path = testdirectory.mkdir('recording')
    recording_file = os.path.join(recording_path.path(), 'test.tar.gz')

    with pytest.raises(NotImplementedError):

        datarecorder.record_data(
            data="{'foo': 2, 'bar': 3}", recording_file=recording_file)
