
import pytest


def pytest_addoption(parser):
    parser.addoption("--type", action="store", default="aks", help="PCP selection: aks/eks")
    parser.addoption("--nocleanup", action="store_true", default=False, help="Disable cleanup")
    parser.addoption("--imageid", action="store", default="", help="Image id name")
    parser.addoption("--bloburi", action="store", default="", help="URL to image blob")


@pytest.fixture(scope="module")
def cmdopt(request):
    config_param = {}
    config_param["type"]=request.config.getoption("--type")
    config_param["imageid"]=request.config.getoption("--imageid")
    config_param["nocleanup"]=request.config.getoption("--nocleanup")
    config_param["bloburi"]=request.config.getoption("--bloburi")
    return config_param