import pytest

import pytest_datarecorder.datarecorder


@pytest.fixture
def datarecorder(request):

    return pytest_datarecorder.datarecorder.DataRecorder()
