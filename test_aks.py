from selenium import webdriver
import configparser
import os
from pageobjects import WelcomePage
from pageobjects import SideBar
from pageobjects import Cluster
from pageobjects import Variables
from pageobjects import Plan
from pageobjects import Deploy
from terraformCmd import TerraformCmd
import uuid
import pytest
import logging
import sys
import time

terraform_cmd = None
driver = None
variables_values = None

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
logger = logging.getLogger(__name__)
logger.addHandler(handler)


@pytest.fixture
def cluster_labels():
    config = configparser.RawConfigParser()
    config.read('test.properties')
    return config.items('cluster_labels')


@pytest.fixture
def prepare_env(cmdopt):
    global terraform_cmd, variables_values, logger
    logger.info("Start setup")
    terraform_cmd = TerraformCmd(logger, os.getcwd()+'/terraform/azure.tf', timeout=1200)
    k8s_version = terraform_cmd.execute_bash_cmd(
        "az aks get-versions --location $ARM_TEST_LOCATION --output table | awk '{print $1}' | grep  '^[0-9]' | grep -v 'preview' | head -n 1")
    variables_values = {
        'subscription_id': os.environ.get('ARM_SUBSCRIPTION_ID'),
        "location": os.environ.get('ARM_TEST_LOCATION'),
        "client_id": os.environ.get('ARM_CLIENT_ID'),
        "client_secret": os.environ.get('ARM_CLIENT_SECRET'),
        "tenant_id": os.environ.get('ARM_TENANT_ID'),
        "ssh_username": 'openqa',
        "admin_password": str(uuid.uuid4()),
        "dns_zone_name": "anton.bear454.codes",
        "cap_domain": "aks{}.anton.bear454.codes".format(str(uuid.uuid4())[:3]),
        "email": "akstest@suse.com",
        "dns_zone_resource_group": "AKS-testing-for-persistent-dns-zone",
        "k8s_version": k8s_version}
    if "AKS_TEST_SSH_PULIC_KEY" in os.environ:
        variables_values["ssh_public_key"] = os.environ.get(
            'AKS_TEST_SSH_PULIC_KEY')
    else:
        variables_values["ssh_public_key"] = "{}/.ssh/id_rsa.pub".format(
            os.environ.get('HOME'))
    logger.info("Defining variables {}".format(variables_values))
    tf_vars = ['ssh_file=' + variables_values['ssh_public_key']]
    if cmdopt["imageid"]:
        tf_vars.append('image_id={}'.format(cmdopt["imageid"]))
    if cmdopt["bloburi"]:
        tf_vars.append('bloburi={}'.format(cmdopt["bloburi"]))
    terraform_cmd.update_tf_vars(tf_vars)
    terraform_cmd.deploy()
    # according to .tf file resource_group name is the same as vm_name
    variables_values['resource_group'] = terraform_cmd.get_output('vm_name')
    logger.info("{} added as variables_values['resource_group']".format(
        variables_values['resource_group']))
    yield {"username": variables_values['resource_group'],
           "pw": variables_values['subscription_id'],
           "ip": terraform_cmd.get_output('public_ip')}
    if cmdopt["nocleanup"]:
        logger.info("--nocleanup option was specified so leaving environment")
    else:
        logger.info("Teardown after test")
        terraform_cmd.clean()
        driver.quit()


def test_simpleFlow(prepare_env, cluster_labels):
    global driver, variables_values
    driver = webdriver.Firefox(service_log_path='/tmp/geckodriver.log')
    """
        sometimes terraform reports success some time before blue-horizon
        actually ready to process requests.
        Ofc there are much better ways to handle this but for now we will just sleep
    """
    time.sleep(60)
    final_url = "http://{}:{}@{}/".format(
        prepare_env["username"], prepare_env["pw"], prepare_env["ip"])
    logger.info("Navigating to %s", final_url)
    driver.get(final_url)
    driver.implicitly_wait(5)
    driver.maximize_window()
    SideBar(driver, logger).page_displayed()
    WelcomePage(driver, logger).go_to_cluster()
    cluster = Cluster(driver, logger)
    cluster.page_displayed()
    cluster.go_to_variables()
    variables = Variables(driver, logger, variables_values, cluster_labels)
    variables.insert_data()
    variables.save_data()
    variables.go_to_plan()
    plan = Plan(driver, logger)
    plan.page_displayed()
    plan.click_plan_button()
    plan.wait_plan_to_finish()
    plan.go_to_deploy()
    deploy = Deploy(driver, logger)
    deploy.page_displayed()
    deploy.click_deploy_button()
    deploy.wait_deploy_to_finish()
    deploy.go_to_next_steps()
