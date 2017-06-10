#!/usr/bin/python
#
# Copyright (c) 2015, Oracle and/or its affiliates. All rights reserved.
#

import time
import string
import pexpect
import re
from basic import *

class ldom(object):

    def __init__(self, name, password, logfile=None):

        self.name = name
        self.password = password
        self.logfile = logfile

    def login(self):

        cmd_list_domain = "ldm list %s | grep %s" % (self.name, self.name)
        output = execute(cmd_list_domain)
        port = output.split()[3].strip()

        cmd = 'telnet 0 ' + str(port)
        cld = pexpect.spawn(cmd)
        cld.send('\r')
        child = pexpect.spawn(cmd)
        if self.logfile is not None:
            child.logfile = open('%s' % self.logfile, 'a+')
        child.send('\r')
        prompts = ['console login:', 'Password:', '~#',
                   pexpect.TIMEOUT, pexpect.EOF, "You do not have write access"]
        while True:
            try:
                i = child.expect(prompts,timeout=300)
            except:
                raise LoginException("Failed to login due to null expect reason")
            if i == 0:
                child.sendline('root')
            elif i == 1:
                child.sendline(self.password)
            elif i == 2:
                cld.close()
                return child
            elif i == 3:
                raise LoginException("Failed to login due to incorrect password or TIMEOUT")
            elif i == 4:
                raise LoginException("Failed to login due to EOF")
            elif i == 5:
                child.send('~wy\r')

    def sendcmd(self, cmd, expectation='~#', timeout=60):
        cldconsole = self.login()
        cldconsole.sendline(cmd)
        cldconsole.send('\r')
        try:
            cldconsole.expect(expectation, timeout)
        except Exception, e:
            raise Exception("Failed to execute [%s] in %s due to:\n %s" % (cmd, self.name, e))
        cldconsole.close()
        time.sleep(0.2)

    def retsend_one_line(self, cmd, expectation='~#',timeout=60):
        cldconsole = self.login()
        if expectation == '~#':
            expectation = 'root@.*:~#'
        cldconsole.sendline(cmd)
        try:
            cldconsole.expect(expectation, timeout)
        except Exception, e:
            raise Exception("Failed to execute [%s] in domain due to:\n %s" % (cmd, e))
        cldconsole.sendline("echo $?")

        i = cldconsole.expect(['0', '1', pexpect.TIMEOUT, pexpect.EOF], timeout)
        if i != 0:
            raise RetExecuteException("Execution of [%s] failed in io domain" % cmd)

        else:
            cldconsole.sendline(cmd)
            cldconsole.readline()
            cldconsole.readline()
            output = cldconsole.readline()
        cldconsole.close()

    def retsend(self, cmd, expectation='~#', timeout=60):
        cldconsole = self.login()
        if expectation == '~#':
            expectation = 'root@.*:~#'
        cldconsole.sendline(cmd)
        cmd_clear = cmd
        cldconsole.expect(cmd_clear) #clear the echo of the command once send
        try:
            cldconsole.expect(expectation, timeout)
        except Exception, e:
            raise Exception("Failed to execute [%s] in %s due to:\n %s" % (cmd, self.name, e))
        output = cldconsole.before
        output = output.strip('cmd_clear').strip('\r\n')
        cldconsole.sendline('echo $?')
        i = cldconsole.expect(['0', '1', pexpect.TIMEOUT, pexpect.EOF,],timeout)
        if i != 0:
            raise RetExecuteException("Execution of [%s] failed in %s:\n%s" % (cmd, self.name, output))
        cldconsole.close()
        time.sleep(0.2)
        return output

    def reboot(self, count=1, timeout=600):
        i = 0
        while(i < count):
            self.sendcmd('reboot', timeout=600)
            i = i + 1

    def panic(self, count=1, timeout=600):
        i = 0
        cmd_panic = "echo 'rootdir/W 0'| mdb -kw"
        cmd_get_debug_version = "echo 'log_init::dis' | mdb -k |grep printf |wc -l"
        printf_num_string = self.retsend_one_line(cmd_get_debug_version)
        printf_num = int(printf_num_string.strip())

        if printf_num == 2:
            debug = False
        else:
            debug = True

        if debug:
            cmd_list_domain = "ldm list %s | grep %s" % (self.name, self.name)
            output = execute(cmd_list_domain)
            port = output.split()[3].strip()
            cmd1 = 'telnet 0 '+ str(port)
            while(i < count):
                self.sendcmd(cmd_panic, 'rootdir:')
                cld = pexpect.spawn(cmd1)
                cld.send('\r')
                child = pexpect.spawn(cmd1)
                child.send('\r')
                prompts = ['eset?',pexpect.TIMEOUT, pexpect.EOF, 'You do not have write access']
                while True:
                    try:
                        i = child.expect(prompts,60)
                    except:
                        raise LoginException("Failed to login due to null expect reason")

                    if i == 0:
                        child.sendline('r')
                        try:
                            child.expect(['console login:'],timeout)
                        except Exception, e:
                            raise LoginException(e)
                        else:
                            break
                        finally:
                            cld.close()
                    elif i == 1:
                        raise  LoginException("Failed to login due to incorrect password or TIMEOUT")
                    elif i == 2:
                        raise LoginException("Failed to login due to EOF")
                    elif i == 3:
                        child.send("~wy\r")
                        prompts.pop(i)
                cld.close()
                i = i + 1
        else:
            while (i < count):
                self.sendcmd(cmd_panic, "console login:", timeout)
                cmd_clear_coredump = "rm -rf /var/crash/*"
                self.sendcmd(cmd_clear_coredump)
                i = i + 1