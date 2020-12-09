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
import time
import pickle


seleniumLogger.setLevel(logging.INFO)
urllibLogger.setLevel(logging.INFO)


@pytest.fixture
def prepare_env(cmdopt, logger, ssh_key_file):
    logger.info("Prepare for EKS testing")
    hosted_zone_name = 'antonec2.bear454.codes'
    variables_values = {
        'ssh_username': 'openqa',
        'hosted_zone_name': hosted_zone_name,
        'email': 'akstest@suse.com',
        'no_cleanup': cmdopt['no_cleanup'],
        'cap_domain': "eks{}.{}".format(str(uuid.uuid4())[:3], hosted_zone_name),
        'admin_password': str(uuid.uuid4()),
        'skip_terraform': cmdopt['skip_terraform'],
        'pw': os.environ.get('AWS_OWNER'),
        'region': os.environ.get('AWS_DEFAULT_REGION'),
        'access_key_id': os.environ.get('AWS_ACCESS_KEY_ID'),
        'secret_access_key': os.environ.get('AWS_SECRET_ACCESS_KEY'),
        'keypair_name': os.environ.get('AWS_KEYPAIR_NAME'),
        'cluster_tag_key': 'openqa_created_by',
        'cluster_tag_value': 'blue-horizon'
    }
    if cmdopt["skip_terraform"]:
        with open("vars.dump", "rb") as f:
            from_dump = pickle.load(f)
            variables_values.update(from_dump)
    else:
        terraform_cmd = TerraformCmd(
            logger, os.getcwd()+'/terraform/ec2.tf', timeout=1200)
        logger.info("Defining variables {}".format(variables_values))
        tf_vars = ['ssh_file=' + ssh_key_file]
        if cmdopt["image_id"]:
            tf_vars.append('image_id={}'.format(cmdopt["image_id"]))
        terraform_cmd.update_tf_vars(tf_vars)
        terraform_cmd.deploy()
        # according to .tf file resource_group name is the same as vm_name
        variables_values["username"] = terraform_cmd.get_output('vm_name')
        variables_values['ip'] = terraform_cmd.get_output('public_ip')
        logger.info("{} added as variables_values['username']".format(
            variables_values['username']))
        logger.info("{} added as variables_values['ip']".format(
            variables_values['ip']))
    yield variables_values
    if cmdopt["no_cleanup"]:
        logger.info(
            "--no_cleanup option was specified so leaving environment. And saving details to reuse it")
        for_dump = {
            'username': variables_values['username'],
            'ip': variables_values['ip']
        }
        with open("vars.dump", "wb") as f:
            pickle.dump(for_dump, f)
    elif not cmdopt["skip_terraform"]:
        logger.info("No op for now , read TODO in source code")
        # TODO implement k8s cleanup before uncomment this
        #logger.info("Teardown after test")
        # terraform_cmd.clean()


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
        prepare_env["username"], prepare_env["pw"], prepare_env["ip"])
    logger.info("Navigating to %s", final_url)
    driver.get(final_url)
    driver.implicitly_wait(5)
    driver.maximize_window()
    SideBar(driver, logger).page_displayed()
    WelcomePage(driver, logger).go_to_cluster(prepare_env['skip_terraform'])
    cluster = Cluster(driver, logger)
    cluster.page_displayed('eks')
    cluster.go_to_variables()
    variables = Variables(driver, logger, prepare_env)
    variables.insert_data('eks')
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
