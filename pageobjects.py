import time
import json


class PageObject:

    def __init__(self, driver):
        self.driver = driver

    def get_element(self, xpath):
        return self.driver.find_element_by_xpath(xpath)

    def click_with_js(self, xpath):
        btn_plan = self.get_element(xpath)
        self.driver.execute_script("arguments[0].click();", btn_plan)


class WelcomePage(PageObject):

    def go_to_cluster(self):
        start_setup = self.get_element(
            '//main[@id="content"]//a[@href="/welcome/simple"]')
        start_setup.click()


class SideBar(PageObject):

    def page_displayed(self):
        self.get_element('//nav[@id="sidebar"]')
        self.get_element('//nav/div/a[@href="/welcome"]')
        self.get_element('//nav/div/a[@href="/variables"]')
        self.get_element('//nav/div/a[@href="/plan"]')
        self.get_element('//nav/div/a[@href="/deploy"]')
        self.get_element('//nav/div/a[@href="/wrapup"]')


class Cluster(PageObject):

    def page_displayed(self):
        instance_type_xpath_pattern = '//div[@class="instance-type-box"]/' + \
            'small[contains(text(),"{}")]'
        self.get_element(instance_type_xpath_pattern.format("Standard_DS3_v2"))
        self.get_element(instance_type_xpath_pattern.format("Standard_DS4_v2"))
        self.get_element(instance_type_xpath_pattern.format("Standard_F4s"))
        self.get_element(instance_type_xpath_pattern.format("Standard_F8s"))
        self.get_element(instance_type_xpath_pattern.format("Standard_A4_v2"))
        self.get_element(instance_type_xpath_pattern.format("Standard_A8_v2"))
        instance_cnt = self.get_element('//input[@id="count-display"]')
        assert instance_cnt.get_attribute('value') == "3"

    def go_to_variables(self):
        btn_variables = self.get_element('//button[@id="submit-cluster"]')
        self.driver.execute_script(
            "arguments[0].scrollIntoView(true);", btn_variables)
        btn_variables.click()


class Variables(PageObject):

    input_xpath_template = '//input[@name="variables[{}]"]'

    def __init__(self, driver, values, cluster_labels):
        super().__init__(driver)
        self.values = values
        self.cluster_labels = cluster_labels

    def __insert_value_for(self, key):
        element = self.get_element(
            Variables.input_xpath_template.format(key))
        element.send_keys(self.values[key])

    def __insert_public_key(self):
        with open(self.values['ssh_public_key'], 'r') as file:
            key = file.read()
            file.close()
            element = self.get_element(
                Variables.input_xpath_template.format('ssh_public_key'))
            element.send_keys(key)

    def __insert_cluster_labels(self):
        for key, value in self.cluster_labels:
            key_input = self.get_element(
                '//input[@id="cluster_labels_new_key"]')
            value_input = self.get_element(
                '//input[@id="cluster_labels_new_value"]')
            key_input.send_keys(key)
            value_input.send_keys(value)
            add_btn = self.get_element(
                '//button[@id="cluster_labels_add_map"]')
            self.driver.execute_script(
                "arguments[0].scrollIntoView(true);", add_btn)
            add_btn.click()
            time.sleep(1)

    def insert_data(self):
        self.__insert_value_for("subscription_id")
        self.__insert_value_for("resource_group")
        self.__insert_value_for("location")
        self.__insert_value_for("client_id")
        self.__insert_value_for("client_secret")
        self.__insert_value_for("tenant_id")
        self.__insert_value_for("ssh_username")
        self.__insert_public_key()
        self.__insert_value_for("cluster_admin_password")
        self.__insert_value_for("uaa_admin_client_secret")
        self.__insert_cluster_labels()
        self.__insert_value_for("dns_zone_name")
        self.__insert_value_for("cap_domain")
        self.__insert_value_for("email")

    def save_data(self):
        self.click_with_js('//button[@id="submit-cluster"]')
        time.sleep(1)
        self.get_element('//div[contains(@class, "alert-success")]')

    def go_to_plan(self):
        self.click_with_js('//main//a[@href="/plan"]')


class Plan(PageObject):

    def page_displayed(self):
        self.get_element(
            '//a[contains(@class,"btn-primary") and @href="/plan"]')
        self.get_element(
            '//a[contains(@class,"disabled") and @href="/deploy"]')

    def click_plan_button(self):
        time.sleep(5)
        self.get_element('//main//a[@href="/plan"]').click()

    def wait_plan_to_finish(self):
        try_count = 120
        while try_count > 0:
            current_code = self.get_element('//code').text
            if current_code:
                plan = json.loads(current_code)
                if plan.get('variables'):
                    break
            elif self.get_element(
                '//div[contains(@class,"alert-danger") and @id="flash"]').\
                    is_displayed():
                raise AssertionError("Plan execution failed")
            print('Waiting')
            try_count = try_count - 1
            time.sleep(5)

    def go_to_deploy(self):
        self.get_element('//main//a[@href="/deploy"]').click()
