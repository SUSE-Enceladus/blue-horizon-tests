from selenium import webdriver
import configparser
import os
from pageobjects import WelcomePage
from pageobjects import SideBar
from pageobjects import Cluster
from pageobjects import Variables
from pageobjects import Plan
from qatrfm.environment import TerraformCmd
import uuid
import pytest
import logging
import sys

terraform_cmd = None
driver = None
variables_values = None

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
logger = logging.getLogger(__name__)
logger.addHandler(handler)


@pytest.fixture
def login():
    global terraform_cmd
    return {"username": variables_values['resource_group'],
            "pw": variables_values['subscription_id'],
            "ip": terraform_cmd.get_output('public_ip')}


@pytest.fixture
def cluster_labels():
    config = configparser.RawConfigParser()
    config.read('test.properties')
    return config.items('cluster_labels')


def setup_function():
    global terraform_cmd, variables_values, logger
    logger.info("Start setup")
    variables_values = {
        'subscription_id': os.environ.get('ARM_SUBSCRIPTION_ID'),
        "location": os.environ.get('ARM_TEST_LOCATION'),
        "client_id": os.environ.get('ARM_CLIENT_ID'),
        "client_secret": os.environ.get('ARM_CLIENT_SECRET'),
        "tenant_id": os.environ.get('ARM_TENANT_ID'),
        "ssh_username": 'openqa',
        "cluster_admin_password": str(uuid.uuid4()),
        "uaa_admin_client_secret": str(uuid.uuid4()),
        "dns_zone_name": "openqa.com",
        "cap_domain": "cap.openqa.com",
        "email": "akstest@suse.com"}
    if "AKS_TEST_SSH_PULIC_KEY" in os.environ:
        variables_values["ssh_public_key"] = os.environ.get(
            'AKS_TEST_SSH_PULIC_KEY')
    else:
        variables_values["ssh_public_key"] = "{}/.ssh/id_rsa.pub".format(
            os.environ.get('HOME'))
    logger.info("Defining variables {}".format(variables_values))
    terraform_cmd = TerraformCmd(
        os.getcwd()+'/terraform/azure.tf',
        ['ssh_file=' + variables_values['ssh_public_key']])
    terraform_cmd.deploy()
    # according to .tf file resource_group name is the same as vm_name
    variables_values['resource_group'] = terraform_cmd.get_output('vm_name')
    logger.info("{} added as variables_values['resource_group']".format(
        variables_values['resource_group']))


def teardown_function():
    global driver, terraform_cmd
    logger.info("Teardown after test")
    terraform_cmd.clean()
    driver.quit()


def test_simpleFlow(login, cluster_labels):
    global driver, variables_values
    driver = webdriver.Firefox(service_log_path='/tmp/geckodriver.log')
    final_url = "http://{}:{}@{}/".format(
        login["username"], login["pw"], login["ip"])
    logger.info("Navigating to %s", final_url)
    driver.get(final_url)
    driver.implicitly_wait(5)
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
    plan = Plan(driver)
    plan.page_displayed()
    plan.click_plan_button()
    plan.wait_plan_to_finish()
    plan.go_to_deploy()
