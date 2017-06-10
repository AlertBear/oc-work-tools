#!/usr/bin/python
#
# Copyright (c) 2015, 2016, Oracle and/or its affiliates. All rights reserved.
#


import time
import re
import pexpect
import os
from basic import *


class Ldom(object):

    def __init__(self, name, password, port, record=False):
        self.name = name
        self.password = password  # Telnet root password
        self.port = port  # Console port
        self.record = record

    def login(self):
        cmd_telnet = 'telnet 0 ' + str(self.port)
        cld = pexpect.spawn(cmd_telnet)
        cld.send('\r')
        child = pexpect.spawn(cmd_telnet)

        # Save the interaction log, test user could review to check the whole
        # process.
        if self.record:
            interact_log = os.getenv("INT_LOG")
            child.logfile = open(interact_log, 'a+')

        child.send('\r')
        prompts = [
            'console login:',
            'Password:',
            '~#',
            pexpect.TIMEOUT,
            pexpect.EOF,
            'You do not have write access']
        while True:
            try:
                i = child.expect(prompts, timeout=300)
            except Exception:
                raise LoginException(
                    "Failed to login %s due to null expect reason" %
                    self.name)
            if i == 0:
                child.sendline('root')
            elif i == 1:
                child.sendline(self.password)
            elif i == 2:
                cld.close()
                return child
            elif i == 3:
                raise LoginException(
                    "Failed to login %s due to incorrect password or TIMEOUT" %
                    self.name)
            elif i == 4:
                raise LoginException("Failed to login %s due to EOF" % self.name)
            elif i == 5:
                child.send('~wy\r')

    def sendcmd(self, cmd, expectation='~#', timeout=60, check=True):
        """
        Purpose:
            Execute the command in this domain without any output
        Arguments:
            cmd - Command to be executed
            expectation - Expect the display after the execution
            timeout - Exceed the timeout during the execution will
                raise the timeout exception
            check - True: Check whether the execution be successful or not
                    False: No check after the execution
        Return:
            None
        """
        cldconsole = self.login()
        cldconsole.sendline(cmd)
        try:
            cldconsole.expect(expectation, timeout)
        except Exception as e:
            raise ExecuteException(
                "Execution of [{0}] in {1} failed due to:\n{2}".format(
                    cmd,
                    self.name,
                    e))
        if check:
            # Check to ensure the command has been successfully executed
            cldconsole.sendline('echo $?')
            i = cldconsole.expect(
                ['0', '1', pexpect.TIMEOUT, pexpect.EOF], timeout)
            if i != 0:
                raise ExecuteException(
                    "Execution of [{0}] failed in {1}".format(
                        cmd,
                        self.name))
        cldconsole.close()
        time.sleep(0.2)

    def retsend_one_line(self, cmd, expectation='~#', timeout=60):
        """
        Purpose:
            Get the execution output of a command in domain,
            ensure there is only one line of the output
        Arguments:
            cmd - Command to be executed
            expectation - Expect the display after the execution
            timeout - Exceed the timeout during the execution will
                raise the timeout exception
        Return:
            output - The output of the execution in domain
        """
        cldconsole = self.login()
        if expectation == '~#':
            expectation = 'root@.*:~#'
        cldconsole.sendline(cmd)
        try:
            cldconsole.expect(expectation, timeout)
        except Exception as e:
            raise Exception(
                "Execution of [%s] failed in %s due to:\n %s" %
                (cmd, self.name, e))
        cldconsole.sendline('echo $?')
        i = cldconsole.expect(
            ['0', '1', pexpect.TIMEOUT, pexpect.EOF], timeout)
        if i != 0:
            raise ReturnException(
                "Execution of [%s] failed in %s" % (cmd, self.name))
        else:
            cldconsole.sendline(cmd)
            cldconsole.readline()
            cldconsole.readline()
            output = cldconsole.readline()
        cldconsole.close()
        return output

    def retsend(self, cmd, expectation='~#', timeout=60, check=True):
        """
        Purpose:
            Get the execution output of a command in domain
        Arguments:
            cmd - Command to be executed
            expectation - Expect the display after the execution
            timeout - Exceed the timeout during the execution will
                raise the timeout exception
        Return:
            output - The output of the execution in domain
        """
        cldconsole = self.login()
        if expectation == '~#':
            expectation = 'root@.*:~#'
        cldconsole.sendline(cmd)
        cmd_clear = cmd
        # Clear the echo of the command once send
        cldconsole.expect(cmd_clear)
        try:
            cldconsole.expect(expectation, timeout)
        except Exception as e:
            raise Exception(
                "Failed to execute [%s] in domain due to:\n %s" % (cmd, e))
        output = cldconsole.before
        output = output.strip(cmd_clear).strip('\r\n')
        if check:
            cldconsole.sendline('echo $?')
            i = cldconsole.expect(
                ['0', '1', pexpect.TIMEOUT, pexpect.EOF], timeout)
            if i != 0:
                raise ReturnException(
                    "Execution of [%s] failed in %s:\n%s" %
                    (cmd, self.name, output))
        cldconsole.close()
        time.sleep(0.2)
        return output

    def reboot(self, count=1, timeout=600):
        """
        Purpose:
            Reboot the domain
        Arguments:
            count - Reboot times
            timeout - If domain doesn't reboot to normal status
                in timeout seconds, will trigger a Exception
        Return:
            None
        """
        i = 0
        cmd = 'reboot'
        while i < count:
            self.sendcmd(cmd, 'console login:', timeout, check=False)
            i += 1

    def panic(self, count=1, timeout=600):
        """
        Purpose:
            Panic the domain
        Arguments:
            count - Panic times
            timeout - If domain doesn't boot to normal status in timeout seconds,
                will trigger a Exception
        Return:
            None
        """
        i = 0
        cmd_panic = 'echo "rootdir/W 0" | mdb -kw'
        # Get debug version by check the printf number in mdb,
        # if num == 2 ,debug =False, else num = 3, debug =True
        cmd_get_debug_version = 'echo "log_init::dis" | mdb -k |grep printf |wc -l'
        printf_num_string = self.retsend_one_line(cmd_get_debug_version)
        printf_num = int(printf_num_string.strip())
        if printf_num == 2:
            debug = False
        else:
            debug = True
        # Test system is a debug one
        if debug:
            # "eset?" may appear
            cmd_telnet = 'telnet 0 ' + str(self.port)
            while i < count:
                self.sendcmd(cmd_panic, 'rootdir:')
                cld = pexpect.spawn(cmd_telnet)
                cld.send('\r')
                child = pexpect.spawn(cmd_telnet)
                child.send('\r')
                prompts = [
                    'eset?',
                    pexpect.TIMEOUT,
                    pexpect.EOF,
                    'You do not have write access']
                while True:
                    try:
                        i = child.expect(prompts, 60)
                    except Exception:
                        raise LoginException(
                            "Failed to login %s due to null expect reason" %
                            self.name)
                    if i == 0:
                        child.sendline('r')
                        try:
                            child.expect(['console login:'], timeout)
                        except Exception as e:
                            raise LoginException(e)
                        else:
                            break
                        finally:
                            cld.close()
                    elif i == 1:
                        raise LoginException(
                            "Failed to login %s due to incorrect password or TIMEOUT" %
                            self.name)
                    elif i == 2:
                        raise LoginException(
                            "Failed to login %s due to EOF" % self.name)
                    elif i == 3:
                        child.send('~wy\r')
                        prompts.pop(i)
                cld.close()
                i += 1
        # Test system is not a debug one
        else:
            # Continue panic will reduce the disk space, need delete the newly
            # generated core dump file
            while i < count:
                # Delete the old crash list file
                prev_crash_list = '/var/tmp/fcior/tmp/prev_crash_list'
                post_crash_list = '/var/tmp/fcior/tmp/post_crash_list'
                cmd_delete_compare_file = "rm -f %s %s" % (
                    prev_crash_list, post_crash_list)
                execute(cmd_delete_compare_file)

                # Create the new crash list file before panic
                cmd_touch_prev_crash_list = "touch %s" % prev_crash_list
                execute(cmd_touch_prev_crash_list)
                # Get all the file under /var/crash/ in domain before panic
                cmd_list_prev_crash_dump = "ls /var/crash/"
                try:
                    output_list_prev_crash_dump = self.retsend(
                        cmd_list_prev_crash_dump)
                except ReturnException:
                    output_list_prev_crash_dump = None
                if output_list_prev_crash_dump is None:
                    has_prev_crash = False
                else:
                    if re.search(r'.', output_list_prev_crash_dump): 
                        has_prev_crash = True
                        with open(prev_crash_list, 'r+') as fo:
                            fo.write(output_list_prev_crash_dump)
                    else:
                        has_prev_crash = False

                # Panic the system
                self.sendcmd(cmd_panic, 'console login:', timeout, check=False)

                # If no crash dump before panic
                if not has_prev_crash:
                    cmd = "rm -rf /var/crash/*"
                    print cmd 
                    self.sendcmd(cmd, check=False)
                else:
                    # Create the new crash list after panic
                    cmd_touch_post_crash_list = "touch %s" % post_crash_list
                    execute(cmd_touch_post_crash_list)

                    # Get the file under /var/crash/ after panic
                    cmd_list_post_crash_dump = "ls /var/crash/"
                    try:
                        output_list_post_crash_dump = self.retsend(
                            cmd_list_post_crash_dump)
                    except ReturnException:
                        output_list_post_crash_dump = None
                    if output_list_post_crash_dump is None:
                        pass
                    else:
                        with open(post_crash_list, 'r+') as fo:
                            fo.write(output_list_post_crash_dump)

                    # Get the newly generated coredump file according to diff two
                    # files above
                    output_diff_two_file = None

                    with open(prev_crash_list, 'r') as prev:
                        with open(post_crash_list, 'r') as post:
                            for fprev in prev.readlines():
                                for fpost in post.readlines():
                                    for file in fpost.split():
                                        file = str(file)
                                        if file not in fprev.split():
                                            output_diff_two_file = file
                                            break

                    # Delete the newly generated coredump file
                    if output_diff_two_file is not None:
                        cmd_get_crashdata = "ls -l /var/crash/{0}".format(
                                output_diff_two_file)
                        output_crashdata = self.retsend(cmd_get_crashdata)
                        crash_data = output_crashdata.split()[-1]
                        cmd_rmdata = "rm -rf /var/crash/{0}".format(crash_data)
                        self.sendcmd(cmd_rmdata, check=False)
                        cmd_clear_coredump = "rm -rf /var/crash/{0}".format(
                            output_diff_two_file)
                        self.sendcmd(cmd_clear_coredump, check=False)
                i += 1
