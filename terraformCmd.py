#!/usr/bin/env python3
#
# Copyright © 2019 SUSE LLC
#
# Copying and distribution of this file, with or without modification,
# are permitted in any medium without royalty provided the copyright
# notice and this notice are preserved.  This file is offered as-is,
# without any warranty.

# Based on https://github.com/jlausuch/qatrfm-lib/blob/master/qatrfm/environment.py

""" Terraform environment

Defines how the Terraform deployment looks like and implements the
appropriate calls to deploy and destroy the environment. All the possible
parameters are passed to the corresponding .tf file

"""

import json
import os
import shutil
import string
import sys
import random
import tempfile
import time
import signal
import subprocess
from threading import Timer

from pathlib import Path


class TrfmCommandTimeout(Exception):
    pass


class TrfmCommandFailed(Exception):
    pass


class TerraformCmd:

    def __init__(self, logger, tf_file, tf_vars=None, timeout=300):
        self.logger = logger
        self.tf_file = tf_file
        self.timeout = timeout
        self.logger.info("Terraform TF file: {}".format(self.tf_file))
        if tf_vars:
            self.update_tf_vars(tf_vars)
        self.workdir = tempfile.mkdtemp()
        self.logger.debug("Using working directory {}".format(self.workdir))
        shutil.copy(self.tf_file, self.workdir + '/env.tf')

    def update_tf_vars(self, vars):
        self.tf_vars = ''
        for v in vars:
            kv = v.split('=', 1)
            if (Path(kv[1]).is_file()):
                kv[1] = Path(kv[1]).resolve()
            self.tf_vars += "-var '{}={}' ".format(kv[0], kv[1])

    def execute_bash_cmd(self, cmd):
        self.logger.debug("Bash command: '{}'".format(cmd))
        output = ''

        def timer_finished(p):
            self.logger.error("Bash command timed out")
            timer.cancel()
            os.killpg(os.getpgid(p.pid), signal.SIGTERM)
            raise TrfmCommandTimeout(output)

        p = subprocess.Popen(cmd, shell=True,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, cwd=self.workdir)
        timer = Timer(self.timeout, timer_finished, args=[p])
        timer.start()
        for line in iter(p.stdout.readline, b''):
            output += line.decode("utf-8")
            self.logger.debug(line.rstrip().decode("utf-8"))
        p.stdout.close()
        retcode = p.wait()
        timer.cancel()
        if (retcode != 0):
            raise TrfmCommandFailed(output)
        return output

    def deploy(self):
        """ Deploy Environment

        It creates the Terraform environment from the given .tf file

        """

        self.logger.info("Deploying Terraform Environment ...")
        self.execute_bash_cmd('terraform init -no-color')
        self.execute_bash_cmd("terraform apply -no-color -input=false -auto-approve {}".format(
            self.tf_vars))

    def clean(self):
        """ Destroys the Terraform environment """
        self.logger.info("Removing Terraform Environment...")
        self.execute_bash_cmd("terraform destroy -input=false -auto-approve {}".format(
            self.tf_vars))
        shutil.rmtree(self.workdir)
        self.logger.success("Environment clean")

    def get_output(self, variable):
        output = self.execute_bash_cmd("terraform output -json")
        return json.loads(output)[variable]['value'][0]
