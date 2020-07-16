Selenium tests covering functionality of https://github.com/SUSE-Enceladus/blue-horizon

Currently supported is only AKS

##Usage

1. Need to create test.properties file with following content

```
[cluster_labels]
openqa_ttl=8000
openqa_created_by=openqa

```
2. Make sure that following environment variables defined :
ARM_SUBSCRIPTION_ID
ARM_TEST_LOCATION
ARM_CLIENT_ID
ARM_CLIENT_SECRET
ARM_TENANT_ID
AKS_TEST_SSH_PULIC_KEY ( in case not defined will fallback to `<home dir of user which execute test>/.ssh/id_rsa.pub`)

3. Execute as regular pytest

Note : running with `pytest -s -v --log-level=DEBUG` will give you some Terraform output describing test environment setup/teardown
Note2 : WebDriver log can be found at `/tmp/geckodriver.log`