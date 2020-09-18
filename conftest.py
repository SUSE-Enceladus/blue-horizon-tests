
import pytest
import logzero
import os


def pytest_addoption(parser):
    parser.addoption("--no_cleanup", action="store_true",
                     default=False, help="Disable cleanup")
    parser.addoption("--skip_terraform", action="store_true",
                     default=False, help="Not invoke terraform at all")
    parser.addoption("--image_id", action="store",
                     default="", help="Image id name")
    parser.addoption("--blob_uri", action="store",
                     default="", help="URL to image blob")


@pytest.fixture(scope="module")
def cmdopt(request):
    config_param = {}
    config_param["image_id"] = request.config.getoption("--image_id")
    config_param["no_cleanup"] = request.config.getoption("--no_cleanup")
    config_param["skip_terraform"] = request.config.getoption(
        "--skip_terraform")
    config_param["blob_uri"] = request.config.getoption("--blob_uri")
    return config_param


@pytest.fixture
def logger():
    return logzero.setup_logger(
        name='bluehorizon', formatter=logzero.LogFormatter(
            fmt='%(color)s%(module)s:%(lineno)d|%(end_color)s %(message)s'))


@pytest.fixture
def ssh_key_file():
    if "SSH_PULIC_KEY_FILE" in os.environ:
        return os.environ.get('SSH_PULIC_KEY_FILE')
    else:
        return "{}/.ssh/id_rsa.pub".format(os.environ.get('HOME'))
