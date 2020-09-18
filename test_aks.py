from selenium import webdriver
import os
from pageobjects import WelcomePage
from pageobjects import SideBar
from pageobjects import Cluster
from pageobjects import Variables
from pageobjects import Plan
from pageobjects import Deploy
from terraformCmd import TerraformCmd
from selenium.webdriver.remote.remote_connection import LOGGER as seleniumLogger
from urllib3.connectionpool import log as urllibLogger
import logging
import uuid
import pytest
import sys
import time
import pickle


seleniumLogger.setLevel(logging.INFO)
urllibLogger.setLevel(logging.INFO)


@pytest.fixture
def prepare_env(cmdopt, logger, ssh_key_file):
    logger.info("Prepare for AKS testing")
    variables_values = {
        'subscription_id': os.environ.get('ARM_SUBSCRIPTION_ID'),
        'location': os.environ.get('ARM_TEST_LOCATION'),
        'client_id': os.environ.get('ARM_CLIENT_ID'),
        'client_secret': os.environ.get('ARM_CLIENT_SECRET'),
        'tenant_id': os.environ.get('ARM_TENANT_ID'),
        'ssh_username': 'openqa',
        'dns_zone_name': 'anton.bear454.codes',
        'email': 'akstest@suse.com',
        'dns_zone_resource_group': 'AKS-testing-for-persistent-dns-zone',
        'no_cleanup': cmdopt['no_cleanup'],
        'skip_terraform': cmdopt['skip_terraform'],
        'cap_domain': "aks{}.anton.bear454.codes".format(str(uuid.uuid4())[:3]),
        'admin_password': str(uuid.uuid4()),
        'ssh_public_key': ssh_key_file
    }
    if cmdopt["skip_terraform"]:
        with open("vars.dump", "rb") as f:
            from_dump = pickle.load(f)
            variables_values.update(from_dump)
    else:
        terraform_cmd = TerraformCmd(
            logger, os.getcwd()+'/terraform/azure.tf', timeout=1200)
        variables_values["k8s_version"] = terraform_cmd.execute_bash_cmd(
            "az aks get-versions --location $ARM_TEST_LOCATION --output table | awk '{print $1}' | grep  '^[0-9]' | grep -v 'preview' | head -n 1")
        logger.info("Defining variables {}".format(variables_values))
        tf_vars = ['ssh_file=' + variables_values['ssh_public_key']]
        if cmdopt["image_id"]:
            tf_vars.append('image_id={}'.format(cmdopt["image_id"]))
        if cmdopt["blob_uri"]:
            tf_vars.append('blob_uri={}'.format(cmdopt["blob_uri"]))
        terraform_cmd.update_tf_vars(tf_vars)
        terraform_cmd.deploy()
        # according to .tf file resource_group name is the same as vm_name
        variables_values['resource_group'] = terraform_cmd.get_output(
            'vm_name')
        variables_values['ip'] = terraform_cmd.get_output('public_ip')
        logger.info("{} added as variables_values['resource_group']".format(
            variables_values['resource_group']))
        logger.info("{} added as variables_values['ip']".format(
            variables_values['ip']))
    yield variables_values
    if cmdopt["no_cleanup"]:
        logger.info(
            "--no_cleanup option was specified so leaving environment. And saving details to reuse it")
        for_dump = {
            'k8s_version': variables_values['k8s_version'],
            'resource_group': variables_values['resource_group'],
            'ip': variables_values['ip']
        }
        with open("vars.dump", "wb") as f:
            pickle.dump(for_dump, f)
    elif not cmdopt["skip_terraform"]:
        logger.info("Teardown after test")
        terraform_cmd.clean()


def test_simpleFlow(prepare_env, logger):
    driver = webdriver.Firefox(service_log_path='/tmp/geckodriver.log')
    """
        sometimes terraform reports success some time before blue-horizon
        actually ready to process requests.
        Ofc there are much better ways to handle this but for now we will just sleep
    """
    if not prepare_env['skip_terraform']:
        time.sleep(60)
    final_url = "http://{}:{}@{}/".format(
        prepare_env["resource_group"], prepare_env["subscription_id"], prepare_env["ip"])
    logger.info("Navigating to %s", final_url)
    driver.get(final_url)
    driver.implicitly_wait(5)
    driver.maximize_window()
    SideBar(driver, logger).page_displayed()
    WelcomePage(driver, logger).go_to_cluster(prepare_env['skip_terraform'])
    cluster = Cluster(driver, logger)
    cluster.page_displayed('aks')
    cluster.go_to_variables()
    variables = Variables(driver, logger, prepare_env)
    variables.insert_data('aks')
    variables.save_data()
    variables.go_to_plan()
    plan = Plan(driver, logger)
    plan.page_displayed(prepare_env['skip_terraform'])
    plan.click_plan_button()
    plan.wait_plan_to_finish()
    plan.go_to_deploy()
    deploy = Deploy(driver, logger)
    deploy.page_displayed()
    deploy.click_deploy_button()
    deploy.wait_deploy_to_finish()
    deploy.go_to_next_steps()
    if not prepare_env["no_cleanup"]:
        driver.quit()
