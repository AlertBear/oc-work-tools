#!/usr/bin/python
#
# Copyright (c) 2015, Oracle and/or its affiliates. All rights reserved.
#

import os
import commands

class ExecuteException(Exception):
	pass

class LoginException(Exception):
	pass

class RetExecuteException(Exception):
	pass

class NullExistException(Exception):
	pass

class NoNeedException(Exception):
	pass

def execute(cmd,exception=ExecuteException):
	(status,output) = commands.getstatusoutput(cmd)
	if status != 0 :
		raise exception("Execution of [%s] failed:\n%s" % (cmd, output))
	return output


