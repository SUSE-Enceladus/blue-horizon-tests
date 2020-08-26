from selenium import webdriver
import os
from pageobjects import WelcomePage
from pageobjects import SideBar
from pageobjects import Cluster
from pageobjects import Variables
from pageobjects import Plan
from pageobjects import Deploy
from terraformCmd import TerraformCmd
from selenium.webdriver.remote.remote_connection import (
    LOGGER as seleniumLogger
)
from urllib3.connectionpool import log as urllibLogger
import logging
import uuid
import pytest
import time
import pickle


seleniumLogger.setLevel(logging.INFO)
urllibLogger.setLevel(logging.INFO)


@pytest.fixture
def prepare_env(cmdopt, logger):
    logger.info("Prepare for GKE testing")
    creds = open(os.environ.get('GCE_SERVICE_ACCOUNT')).read()
    domain = (
        os.environ.get('FQDN') or
        "gke{}.anton.bear454.codes".format(str(uuid.uuid4())[:3])
    )
    email = (
        os.environ.get('EMAIL') or
        'anton.smorodskyi@suse.com'
    )
    variables_values = {
        'project': os.environ.get('GCE_PROJECT'),
        'location': os.environ.get('GCE_TEST_LOCATION'),
        'credentials_json': creds,
        'dns_credentials_json': creds,
        'admin_password': str(uuid.uuid4()),
        'cap_domain': domain,
        'email': email,
        'skip_terraform': cmdopt['skip_terraform'],
        'no_cleanup': cmdopt['no_cleanup'],
    }
    if cmdopt["skip_terraform"]:
        logger.info('skipping terraform')
        with open("vars.dump", "rb") as f:
            from_dump = pickle.load(f)
            variables_values.update(from_dump)
    else:
        terraform_cmd = TerraformCmd(
            logger, os.getcwd()+'/terraform/gce.tf', timeout=1200)
        logger.info("Defining variables {}".format(variables_values))
        tf_vars = ['google_credentials_file=' + os.environ.get('GCE_SERVICE_ACCOUNT')]
        terraform_cmd.update_tf_vars(tf_vars)
        terraform_cmd.deploy()
        variables_values['vm_name'] = terraform_cmd.get_output(
            'vm_name')
        variables_values['ip'] = terraform_cmd.get_output('public_ip')
        variables_values['instance_id'] = terraform_cmd.get_output(
            'instance_id'
        )
        logger.info("{} added as variables_values['vm_name']".format(
            variables_values['vm_name']))
        logger.info("{} added as variables_values['instance_id']".format(
            variables_values['instance_id']))
        logger.info("{} added as variables_values['ip']".format(
            variables_values['ip']))
    yield variables_values
    if cmdopt["no_cleanup"]:
        logger.info(
            "--no_cleanup option was specified so leaving environment."
            "And saving details to reuse it")
        for_dump = {
            'vm_name': variables_values['vm_name'],
            'instance_id': variables_values['instance_id'],
            'ip': variables_values['ip']
        }
        with open("vars.dump", "wb") as f:
            pickle.dump(for_dump, f)
    elif not cmdopt["skip_terraform"]:
        logger.info("Teardown after test")
        terraform_cmd.clean()


def test_simpleFlow(prepare_env, cluster_labels, logger):
    driver = webdriver.Firefox(service_log_path='/tmp/geckodriver.log')
    """
        sometimes terraform reports success some time before blue-horizon
        actually ready to process requests.
        Ofc there are much better ways to handle this but for now
        we will just sleep
    """
    if not prepare_env['skip_terraform']:
        time.sleep(60)
    final_url = "http://{}:{}@{}/".format(
        prepare_env["instance_id"], prepare_env["vm_name"], prepare_env["ip"])
    logger.info("Navigating to %s", final_url)
    driver.get(final_url)
    driver.implicitly_wait(5)
    driver.maximize_window()
    SideBar(driver, logger).page_displayed()
    WelcomePage(driver, logger).go_to_cluster(prepare_env['skip_terraform'])
    cluster = Cluster(driver, logger)
    cluster.page_displayed('gke')
    cluster.go_to_variables()
    variables = Variables(driver, logger, prepare_env, cluster_labels)
    variables.insert_data('gke')
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
