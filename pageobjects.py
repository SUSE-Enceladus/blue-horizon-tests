import time
import datetime
import json
import re
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException, StaleElementReferenceException


class PageObject:

    def __init__(self, driver, logger):
        self.logger = logger
        self.driver = driver
        self.pause_sec = 5

    def get_element(self, xpath, check_existence=False):
        try_count = 20
        while try_count > 0:
            if len(self.driver.find_elements_by_xpath(xpath)) > 0:
                return self.driver.find_element_by_xpath(xpath)
            if check_existence:
                return False
            try_count = try_count - 1
            self.logger.debug("Looking for {}".format(xpath))
            time.sleep(1)
        raise NoSuchElementException(
            msg="Failed to locate element with xpath={}".format(xpath))

    def click_with_js(self, xpath):
        element = self.get_element(xpath)
        self.driver.execute_script("arguments[0].click();", element)

    def wait_for_click(self, xpath):
        element = self.get_element(xpath)
        try_count = 25
        while try_count > 0:
            try:
                element.click()
            except ElementClickInterceptedException:
                self.logger.debug("Can not click on {}".format(xpath))
                time.sleep(1)
                try_count = try_count - 1
            except StaleElementReferenceException:
                self.logger.debug(
                    "Stale element exception for {}".format(xpath))
                element = self.get_element(xpath)
                try_count = try_count - 1
            else:
                return True
        raise ElementClickInterceptedException(
            "Failed to click on {}".format(xpath))


class WelcomePage(PageObject):

    def go_to_cluster(self, reset_session_popup):
        if reset_session_popup:
            self.logger.info(
                'Reusing already created env, so need to close reset session window')
            self.click_with_js('//div[@class="modal-footer"]/a')
        self.wait_for_click(
            '//main[@id="content"]//a[@href="/welcome/simple"]')


class SideBar(PageObject):

    def page_displayed(self):
        self.get_element('//nav[@id="sidebar"]')
        self.get_element('//nav/div/a[@href="/welcome"]')
        self.get_element('//nav/div/a[@href="/variables"]')
        self.get_element('//nav/div/a[@href="/plan"]')
        self.get_element('//nav/div/a[@href="/deploy"]')
        self.get_element('//nav/div/a[@href="/wrapup"]')


class Cluster(PageObject):

    def page_displayed(self, cloud_provider):
        instance_type_xpath_pattern = '//div[@class="instance-type-box"]/' + \
            'small[contains(text(),"{}")]'
        if cloud_provider == 'aks':
            self.get_element(
                instance_type_xpath_pattern.format("Standard_DS3_v2"))
            self.get_element(
                instance_type_xpath_pattern.format("Standard_DS4_v2"))
            self.get_element(
                instance_type_xpath_pattern.format("Standard_F4s"))
            self.get_element(
                instance_type_xpath_pattern.format("Standard_F8s"))
            self.get_element(
                instance_type_xpath_pattern.format("Standard_A4_v2"))
            self.get_element(
                instance_type_xpath_pattern.format("Standard_A8_v2"))
        elif cloud_provider == 'eks':
            self.get_element(instance_type_xpath_pattern.format("t2.xlarge"))
            self.get_element(instance_type_xpath_pattern.format("m4.xlarge"))
            self.get_element(instance_type_xpath_pattern.format("c4.2xlarge"))
            self.get_element(instance_type_xpath_pattern.format("r3.xlarge"))
            self.get_element(instance_type_xpath_pattern.format("i3.xlarge"))
            self.get_element(instance_type_xpath_pattern.format("d2.xlarge"))
        elif cloud_provider == 'gke':
            self.get_element(instance_type_xpath_pattern.format("n1-standard-4"))
            self.get_element(instance_type_xpath_pattern.format("n1-standard-8"))
            self.get_element(instance_type_xpath_pattern.format("n1-highmem-4"))
            self.get_element(instance_type_xpath_pattern.format("n1-highmem-8"))
        instance_cnt = self.get_element('//input[@id="count-display"]')
        assert instance_cnt.get_attribute('value') == "3"

    def go_to_variables(self):
        btn_variables = self.get_element('//button[@id="submit-cluster"]')
        self.driver.execute_script(
            "arguments[0].scrollIntoView(true);", btn_variables)
        btn_variables.click()


class Variables(PageObject):

    input_xpath_template = '//input[@name="variables[{}]"]'

    def __init__(self, driver, logger, values):
        super().__init__(driver, logger)
        self.values = values

    def __insert_value_for(self, key):
        element = self.get_element(
            Variables.input_xpath_template.format(key))
        element.clear()
        element.send_keys(self.values[key])

    def __insert_public_key(self):
        with open(self.values['ssh_public_key'], 'r') as file:
            key = file.read()
            file.close()
            element = self.get_element(
                Variables.input_xpath_template.format('ssh_public_key'))
            element.send_keys(key)

    def __insert_cluster_labels(self):
            add_btn = self.get_element(
                '//button[@id="cluster_labels_add_map"]')
            self.driver.execute_script(
                "arguments[0].scrollIntoView(true);", add_btn)
            key_input = self.get_element(
                '//input[@id="cluster_labels_new_key"]')
            value_input = self.get_element(
                '//input[@id="cluster_labels_new_value"]')
            key_input.send_keys('openqa_created_by')
            value_input.send_keys('blue_horizon')
            add_btn.click()

    def insert_data(self, cloud_provider):
        if cloud_provider == "aks":
            self.__insert_value_for("subscription_id")
            self.__insert_value_for("resource_group")
            self.__insert_value_for("location")
            self.__insert_value_for("k8s_version")
            self.__insert_value_for("client_id")
            self.__insert_value_for("client_secret")
            self.__insert_value_for("tenant_id")
            self.__insert_value_for("ssh_username")
            self.__insert_value_for("dns_zone_resource_group")
            self.__insert_public_key()
            self.__insert_value_for("dns_zone_name")
        elif cloud_provider == 'eks':
            self.__insert_value_for("region")
            self.__insert_value_for("access_key_id")
            self.__insert_value_for("secret_access_key")
            self.__insert_value_for("keypair_name")
            self.__insert_value_for("hosted_zone_name")
        elif cloud_provider == 'gke':
            self.__insert_value_for("project")
            self.__insert_value_for("location")
            self.__insert_value_for("credentials_json")
            self.__insert_value_for("dns_credentials_json")
        self.__insert_value_for("admin_password")
        self.__insert_cluster_labels()
        self.__insert_value_for("cap_domain")
        self.__insert_value_for("email")

    def save_data(self):
        self.click_with_js('//button[@id="submit-cluster"]')
        self.get_element('//div[contains(@class, "alert-success")]')

    def go_to_plan(self):
        self.click_with_js('//main//button[@id="next"]')


class Plan(PageObject):

    def page_displayed(self, deploy_enabled):
        deploy_btn = '//a[contains(@class,"disabled") and @href="/deploy"]'
        if deploy_enabled:
            # in case we reusing already used instance Deploy button will be enabled initially
            deploy_btn = '//a[@href="/deploy"]'

        self.get_element(
            '//a[contains(@class,"btn-primary") and @href="/plan"]')
        self.get_element(deploy_btn)

    def click_plan_button(self):
        self.get_element('//main//a[@href="/plan"]').click()

    def wait_plan_to_finish(self):
        try_count = 120
        plan_passed = False
        while try_count > 0:
            current_code = self.get_element('//code').text
            if current_code:
                try:
                    plan = json.loads(current_code)
                except JSONDecodeError as ex:
                    self.logger.error("[JSONDecodeError] Invalid JSON")
                else:
                    if plan.get('variables'):
                        self.logger.info('Plan completed')
                        plan_passed = True
                        break
            if self.get_element(
                '//div[contains(@class,"alert-danger") and @id="flash"]').\
                    is_displayed():
                raise AssertionError("Plan execution failed")
            self.logger.info('Waiting for plan. {} before timeout'.format(
                datetime.timedelta(seconds=try_count * self.pause_sec)))
            try_count = try_count - 1
            time.sleep(self.pause_sec)
        assert plan_passed, "Plan timed out!"

    def go_to_deploy(self):
        self.click_with_js('//main//a[@href="/deploy"]')


class Deploy(PageObject):

    def page_displayed(self):
        self.get_element(
            '//a[contains(@class,"btn-primary") and @href="/deploy"]')
        self.get_element(
            '//a[contains(@class,"disabled") and @href="/wrapup"]')

    def click_deploy_button(self):
        time.sleep(3)
        self.get_element(
            '//a[contains(@class,"btn-primary") and @href="/deploy"]').click()

    def go_to_next_steps(self):
        self.click_with_js('//main//a[@href="/wrapup"]')

    def wait_deploy_to_finish(self):
        try_count = 400
        deployed = False
        while try_count > 0:
            if "disabled" not in self.get_element('//main//a[@href="/wrapup"]').get_attribute("class"):
                self.logger.info('Next steps not disabled anymore')
                if re.findall(r'Apply complete! Resources: \d{1,2} added, \d{1,2} changed, \d{1,2} destroyed', self.get_element('//code[@id="output"]').text):
                    self.logger.info('Apply completed')
                    deployed = True
                    break
            if self.get_element(
                '//div[contains(@class,"alert-danger") and @id="flash"]').\
                    is_displayed():
                raise AssertionError("Deploy execution failed")
            self.logger.info('Waiting for deploy. {} left before timeout'.format(
                datetime.timedelta(seconds=try_count * self.pause_sec)))
            try_count = try_count - 1
            time.sleep(self.pause_sec)
        assert deployed, "Deploy timed out"
