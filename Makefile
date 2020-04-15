
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

.PHONY: test
test:
	pytest
