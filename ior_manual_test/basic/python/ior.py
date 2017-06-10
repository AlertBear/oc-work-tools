#!/usr/bin/python

import os
import sys
import getopt
import ldom

def usage():
    print "ior.py usages:"
    print "-h, --help: help messages"
    print "-d, --domain: operate on which domain"
    print "-s, --send: send and execute the command"
    print "-r, --return: send the command and get the response"
    print "-t, --timeout: execute the command in timeout"
    print "-l, --logfile: save the interaction log of domain"

def main():
    domain_name = ''
    domain_password = ''
    logfile = None
    send = ''
    retsend = ''
    mtimeout = None
    reboot = False
    panic = False

    shortargs = 'hd:p:s:r:t:l:'
    longargs = ['help', 'domain=', 'password=', 'send=', 'return=', 'timeout=', 'logfile=', 'reboot', 'panic']
    try:
        opts, args = getopt.getopt(sys.argv[1:], shortargs, longargs)
    except getopt.GetoptError, e:
        print e
        usage()
        sys.exit(2)

    for opt, value in opts:
        if opt in ('-h', '--help'):
            usage()
            sys.exit(1)
        elif opt in ('-d', '--domain'):
            domain_name = value
        elif opt in ('-p', '--password'):
            domain_password = value
        elif opt in ('-s', '--sendcmd'):
            send = value
        elif opt in ('-r', '--retsend'):
            retsend = value
        elif opt in ('-t', '--timeout'):
            mtimeout = value
        elif opt in ('-l', '--logfile'):
            logfile = value
        elif opt in ('--reboot'):
            reboot = True
        elif opt in ('--panic'):
            panic = True
        else:
            pass

    domain = ldom.ldom(domain_name, domain_password, logfile)

    if send != '':
        domain.sendcmd(send,timeout=mtimeout)
    if retsend != '':
        output = domain.retsend(retsend,timeout=mtimeout)
        print output
    if reboot:
        domain.reboot()
    if panic:
        domain.panic()

if __name__ == "__main__":
    main()
