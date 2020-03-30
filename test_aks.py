from selenium import webdriver
import configparser
from pageobjects import WelcomePage
from pageobjects import SideBar
from pageobjects import Cluster
from pageobjects import Variables
import pytest


@pytest.fixture
def variables_values():
    config = configparser.RawConfigParser()
    config.read('test.properties')
    keys = ["subscription_id", "resource_group", "location", "client_id", "client_secret", "tenant_id",
            "ssh_username", "ssh_public_key", "cluster_admin_password", "uaa_admin_client_secret", "dns_zone_name", "cap_domain", "email"]
    return dict(map(lambda x: (x, config.get('variables', x)), keys))


@pytest.fixture
def login():
    config = configparser.RawConfigParser()
    config.read('test.properties')
    return {"username": config.get('login', 'username'), "pw": config.get('login', 'pw'), "ip": config.get('login', 'ip')}


@pytest.fixture
def cluster_labels():
    config = configparser.RawConfigParser()
    config.read('test.properties')
    return config.items('cluster_labels')


def test_simpleFlow(login, variables_values, cluster_labels):
    driver = webdriver.Firefox(service_log_path='/tmp/geckodriver.log')
    driver.get(
        "http://{}:{}@{}/".format(login["username"], login["pw"], login["ip"]))
    driver.maximize_window()
    SideBar(driver).page_displayed()
    WelcomePage(driver).go_to_cluster()
    cluster = Cluster(driver)
    cluster.page_displayed()
    cluster.go_to_variables()
    variables = Variables(driver, variables_values, cluster_labels)
    variables.insert_data()
    variables.save_data()
    variables.go_to_plan()
