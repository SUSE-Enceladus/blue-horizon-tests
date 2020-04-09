USERNAME := $(shell id -un)
SSH_KEY := $(shell cat test.properties | grep ssh_public_key= | awk '{split($$0, a, "="); print a[2];}')

.PHONY: all
all: check

.PHONY: prepare
prepare:
	pip install -r requirements.txt
	ifeq (, $(@shell which geckodrivedr))
		$(error "Download latest geckodriver from https://github.com/mozilla/geckodriver/releases and place it in your $$(PATH).")
	endif

.PHONY: check
check:
	flake8 *.py

.PHONY: terraform
terraform:
	(cd terraform && terraform apply -var 'ssh_file=$(SSH_KEY)' -var 'name=$(USERNAME)-blue-horizon-test' -auto-approve -no-color)

.PHONY: terraform-destroy
terraform-destroy:
	(cd terraform && terraform destroy -auto-approve)

.PHONY: test
test: vm_name=$(shell (cd terraform && terraform output -json) | jq -r '.vm_name.value[0]')
test: public_ip=$(shell (cd terraform && terraform output -json) | jq -r '.public_ip.value[0]')
test:
	sed -i "/^subscription_id=/c\subscription_id=${ARM_SUBSCRIPTION_ID}" test.properties
	sed -i "/^pw=/c\pw=${ARM_SUBSCRIPTION_ID}" test.properties
	sed -i "/^username=/c\username=$(vm_name)" test.properties
	sed -i "/^client_id=/c\client_id=${ARM_CLIENT_ID}" test.properties
	sed -i "/^client_secret=/c\client_secret=${ARM_CLIENT_SECRET}" test.properties
	sed -i "/^tenant_id=/c\tenant_id=${ARM_TENANT_ID}" test.properties
	sed -i "/^ip=/c\ip=$(public_ip)" test.properties
	sed -i "/^resource_group=/c\resource_group=$(vm_name)" test.properties
	pytest
