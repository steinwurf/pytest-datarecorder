import pytest_datarecorder
import os
import pytest
import pathlib
import json
import pandas as pd
import matplotlib.pyplot as plt


def test_record_json(testdirectory, datarecorder):

    recording_path = testdirectory.mkdir("recording")
    recording_file = os.path.join(recording_path.path(), "test.json")

    datarecorder.record_data(data={"foo": 2, "bar": 3}, recording_file=recording_file)

    # Calling again with same data should be fine
    datarecorder.record_data(data={"foo": 2, "bar": 3}, recording_file=recording_file)

    datarecorder.record_data(data={"bar": 3, "foo": 2}, recording_file=recording_file)

    # With new data should raise
    with pytest.raises(pytest_datarecorder.datarecorder.DataRecorderError):
        datarecorder.record_data(
            data={"foo": 3, "bar": 3}, recording_file=recording_file
        )


def test_record_rst(testdirectory, datarecorder):

    recording_path = testdirectory.mkdir("recording")
    recording_file = os.path.join(recording_path.path(), "test.rst")

    datarecorder.record_data(data="Hello\n=====\nWorld", recording_file=recording_file)

    # Calling again with same data should be fine
    datarecorder.record_data(data="Hello\n=====\nWorld", recording_file=recording_file)

    # With new data should raise
    with pytest.raises(pytest_datarecorder.datarecorder.DataRecorderError):
        datarecorder.record_data(
            data="Hello\n=====\nwurfapi", recording_file=recording_file
        )


def test_record_no_mapping(testdirectory, datarecorder):

    recording_path = testdirectory.mkdir("recording")
    recording_file = os.path.join(recording_path.path(), "test.tar.gz")

    with pytest.raises(NotImplementedError):

        datarecorder.record_data(
            data="{'foo': 2, 'bar': 3}", recording_file=recording_file
        )


def test_file_record(testdirectory, datarecorder):

    recording_dir = testdirectory.mkdir("recording")
    recording_file = os.path.join(recording_dir.path(), "test.json")

    # Check that the recording is made
    assert not recording_dir.contains_file("test.json")

    datarecorder.record_file(
        data_file="test/data/test.json", recording_file=recording_file
    )

    # Check that we match the recording
    assert recording_dir.contains_file("test.json")

    datarecorder.record_file(
        data_file="test/data/test.json", recording_file=recording_file
    )


def test_record_pathlib_path(testdirectory, datarecorder):

    recording_dir = testdirectory.mkdir("recording")
    recording_file = os.path.join(recording_dir.path(), "test.json")

    # Check that the recording is made
    assert not recording_dir.contains_file("test.json")

    data = [pathlib.Path("test/data/test.json")]

    datarecorder.record_data(data=data, recording_file=recording_file)

    # Check that we match the recording
    assert recording_dir.contains_file("test.json")

    datarecorder.record_data(data=data, recording_file=recording_file)


def test_recording_type(testdirectory, datarecorder):

    input_dir = testdirectory.mkdir("input")
    input_file = input_dir.write_text(
        filename="noextension", data="hello", encoding="utf-8"
    )

    recording_dir = testdirectory.mkdir("recording")
    recording_file = os.path.join(recording_dir.path(), "noextension")

    # Check that the recording is made
    assert not recording_dir.contains_file("noextension")

    datarecorder.record_file(
        data_file=input_file, recording_file=recording_file, recording_type="txt"
    )

    # Check that we match the recording
    assert recording_dir.contains_file("noextension")


def test_record_mismatch(testdirectory, datarecorder):

    recording_path = testdirectory.mkdir("recording")
    mismatch_dir = testdirectory.mkdir("mismatch")
    recording_file = os.path.join(recording_path.path(), "test.json")

    datarecorder.record_data(data=[1, 2, 3, 4, 5], recording_file=recording_file)

    # Calling again with same data should be fine
    datarecorder.record_data(data=[1, 2, 3, 4, 5], recording_file=recording_file)

    mismatch_index = []

    def on_mismatch(mismatch_data, recording_data, mismatch_dir):

        mismatch_data = json.loads(mismatch_data)
        recording_data = json.loads(recording_data)

        for i, (d, r) in enumerate(zip(mismatch_data, recording_data)):
            if d != r:
                mismatch_index.append(i)

        # Create the DataFrame
        df = pd.DataFrame({"X": mismatch_data, "Y": recording_data})

        plt.scatter(
            list(range(len(mismatch_data))), mismatch_data, label="Mismatch", marker="x"
        )

        plt.scatter(
            list(range(len(recording_data))),
            recording_data,
            label="Recording",
            marker="+",
        )
        plt.legend()

        # Save the figure as a PNG image
        plt.savefig(os.path.join(mismatch_dir, "scatter.png"))

        return (
            f"Data mismatch at index {mismatch_index}"
            f" see {os.path.join(mismatch_dir, 'scatter.png')} for details"
        )

    with pytest.raises(pytest_datarecorder.datarecorder.DataRecorderError) as e:
        datarecorder.record_data(
            data=[5, 2, 3, 1, 5],
            recording_file=recording_file,
            mismatch_callback=on_mismatch,
            mismatch_dir=mismatch_dir.path(),
        )

    assert "Data mismatch at index [0, 3]" in str(e.value)
    assert mismatch_index == [0, 3]

    # Check that the mismatch directory contains the files
    assert mismatch_dir.contains_file("scatter.png")
