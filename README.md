Selenium tests covering functionality of https://github.com/SUSE-Enceladus/blue-horizon

Currently AKS and EKS are supported

##Usage

1. Need to create test.properties file with following content

```
[cluster_labels]
openqa_ttl=8000
openqa_created_by=openqa

```
2. Make sure that following environment variables defined :

SSH_PULIC_KEY_FILE - points to ssh public key **file**. When variable is not defined will fallback to `<home dir of user which execute test>/.ssh/id_rsa.pub`.
In AKS it is used two times : one as access key to blue-horizon VM and second for k8s cluster creation. In EKS only for blue-horizon VM

In case of AKS :
ARM_SUBSCRIPTION_ID
ARM_TEST_LOCATION
ARM_CLIENT_ID
ARM_CLIENT_SECRET
ARM_TENANT_ID

In case of EKS :

AWS_OWNER - AWS account number
AWS_DEFAULT_REGION - region will be used to create k8s cluster . Region for blue-horizon VM is currently hard coded in terraform file
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
AWS_KEYPAIR_NAME - name of Key Pair entity which will be used for k8s cluster. Should be created before test execution. Also make sure that it is created in the AWS_DEFAULT_REGION

3. Execute as regular pytest

Note : running with `pytest -s -v --log-level=DEBUG` will give you some Terraform output describing test environment setup/teardown
Note2 : WebDriver log can be found at `/tmp/geckodriver.log`
Note 3: check conftest.py for extra parameters which can be used