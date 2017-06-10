#!/usr/bin/python
# coding=utf-8

import cookielib
import urllib2
import urllib
import re
import time

class Lrt:

    def __init__(self, username, password, machine_dict):

        self.url_index = 'https://lrt.us.oracle.com/'
        self.url_login = 'https://login.oracle.com'
        self.url_reserve = ''

        self.username = username
        self.password = password
        self.machine_dict = machine_dict

        self.cj = cookielib.LWPCookieJar()

        self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cj), urllib2.HTTPHandler)
        self.opener.addheaders = [('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:36.0) \
            Gecko/20100101 Firefox/36.0'), ('Connection','keep-alive')]
        urllib2.install_opener(self.opener)

    def login(self):
        tryLogin_resp = self.opener.open(self.url_index)
        url = tryLogin_resp.geturl()

        if re.match(self.url_login, url):
            cont = tryLogin_resp.read()
            rh = re.compile(r'<input')
            rkv = re.compile(r'^.* name="(.*)" value="(.*)"$')
            kvlist = [rkv.sub(r'\1 \2',i).split(' ') for i in cont.split('>') if rh.match(i)]
            kvdict0 = dict(kvlist)
            kvdict={}
            kvdict['OAM_REQ'] = kvdict0['OAM_REQ']
            kvdict['locale'] = kvdict0['locale']
            kvdict['request_id'] = kvdict0['request_id']
            kvdict['site2pstoretoken'] = kvdict0['site2pstoretoken']
            kvdict['v'] = kvdict0['v']
            kvdict['ssousername'] = self.username
            kvdict['password'] = self.password
            postLoginData = urllib.urlencode(kvdict)
            url_doLogin = 'https://login.oracle.com/oam/server/sso/auth_cred_submit'
            resp_doLogin = self.opener.open(url_doLogin, postLoginData)
            if re.match('https://lrt.us.oracle.com/', resp_doLogin.geturl()):
                pass
                   #print('Login success')
            else :
                 print('Login fail,please check the network')
        else:
            print('Already logged in')

    def reserveMachine(self):
        url_reserve = 'https://lrt.us.oracle.com/reserve.php'
        #postReserveData = 'reserve=26830&number_of_days=21&project_list=---+Select+From+This+List+---&
            # project=hcts&comments=test&Reserve=Reserve+colorwine'
        for machine in self.machine_dict.keys():
            entry_id = self.machine_dict.get(machine).get('entry_id')
            days = self.machine_dict.get(machine).get('days')
            project = self.machine_dict.get(machine).get('project')
            comment = self.machine_dict.get(machine).get('comment')
            project_list = '--- Select From This List ---'
            reserve_machine = 'Reserve %s' % machine

            postReserveData = urllib.urlencode({'reserve': entry_id,
                                                'number_of_days': days,
                                                'project': project,
                                                'project_list': project_list,
                                                'comments': comment,
                                                'Reserve': reserve_machine})
            url_reserve_success = 'https://lrt.us.oracle.com/system_detail.php?entry=%s' % entry_id

            self.opener.addheaders = [('Referer', 'https://lrt.us.oracle.com/reserve.php?entry=%s' % entry_id)]
            reserve_resp = self.opener.open(url_reserve, postReserveData)
            #print(reserve_resp.read(), reserve_resp.geturl())
            reserve_resp_url = reserve_resp.geturl()
            if re.search(r'system_detail', reserve_resp_url):
                print('Reserve %s success for next %s days' % (machine, days))
                print('See detail in: %s' % reserve_resp_url)
            else:
                print 'Failed to reserve %s, responding output:\n %s' % (machine, reserve_resp.read())
            time.sleep(5)

    def updateMachine(self):
        for machine in self.machine_dict.keys():
            entry_id = self.machine_dict.get(machine).get('entry_id')
            days = self.machine_dict.get(machine).get('days')
            comment = self.machine_dict.get(machine).get('comment')
            project = self.machine_dict.get(machine).get('project')
            url_update = 'https://lrt.us.oracle.com/release_or_change.php?entry=%s' % entry_id
            #entry=26830&Update=Update&number_of_days=7&reserved_comment=tests&reserved_project=hcts&
                # project_list=--+Select+--&from=https%3A%2F%2Flrt.us.oracle.com%2Fsystem_detail.php%3Fentry%3D26830
            postUpdateData = urllib.urlencode({'entry': entry_id,
                                               'Update':'Update',
                                               'number of days': days,
                                               'reserved_comment': comment,
                                               'reserved_project': project,
                                               'project list': '-- Select --',
                                               'from': 'https://lrt.us.oracle.com/system_detail.php?entry=%s' % entry_id}
                                             )
            url_update_success = 'https://lrt.us.oracle.com/system_detail.php?entry=%s' % entry_id

            self.opener.addheaders = [('Referer','https://lrt.us.oracle.com/release_or_change.php?entry=%s' % entry_id)]
            update_resp = self.opener.open(url_update, postUpdateData)
            #print(update_resp.read(), update_resp.geturl())
            update_resp_url = update_resp.geturl()

            if re.search(r'system_detail', update_resp_url):
                print('Update %s succes for next %s days' % (machine, days))
                print('See detail in: %s' % update_resp_url)
            else:
                print 'Failed to update %s, responding output:\n %s' % (machine, update_resp.read())
            time.sleep(5)

    def releaseMachine(self):
        for machine in self.machine_dict.keys():
            entry_id = self.machine_dict.get(machine).get('entry_id')
            days = self.machine_dict.get(machine).get('days')
            comment = self.machine_dict.get(machine).get('comment')
            project = self.machine_dict.get(machine).get('project')
            url_release = 'https://lrt.us.oracle.com/release_or_change.php?entry=%s' % entry_id
            #entry=26830&Update=Update&number_of_days=7&reserved_comment=tests&reserved_project=hcts&
            # project_list=--+Select+--&from=https%3A%2F%2Flrt.us.oracle.com%2Fsystem_detail.php%3Fentry%3D26830
            postReleaseData = urllib.urlencode({'entry': entry_id,
                                                'Release': 'Release',
                                                'number of days': days,
                                                'reserved comment': comment,
                                                'reserved project': project,
                                                'project list': '-- Select --',
                                                'from': 'https://lrt.us.oracle.com/system_detail.php?entry=%s' % entry_id}
                                               )
            url_release_success = 'https://lrt.us.oracle.com/system_detail.php?entry=%s' % entry_id

            self.opener.addheaders = [('Referer','https://lrt.us.oracle.com/release_or_change.php?entry=%s' % entry_id)]
            release_resp = self.opener.open(url_release, postReleaseData)
            #print(release_resp.read(), release_resp.geturl())
            release_resp_url = release_resp.geturl()
            if re.search(r'system_detail', release_resp_url):
                print('Release %s succes' % machine)
                print('See detail in: %s '% release_resp_url)
            else:
                print 'Failed to release %s, responding output:\n %s' % (machine, release_resp.read())
            time.sleep(5)