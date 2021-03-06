#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import argparse
import os
import sys
import ConfigParser
import smtplib
import mistune
import shutil
from datetime import datetime
from email.mime.text import MIMEText
from email.header import Header
from pydash.objects import defaults
from colorama import init, Fore

APP_DESC = '''
Author:         Nix
Github:         https://github.com/WellerQu/weekday
Version:        1.0.0
'''

init(autoreset=True)


def main():
    if len(sys.argv) < 2:
        sys.argv.append('-h')

    args = initializeArguments()
    tmpFileName = ('%s/.weekday/current.rp' % os.environ['HOME'])
    confFileName = ('%s/.weekday/conf' % os.environ['HOME'])
    conf = loadConfig(confFileName)
    dir = os.path.dirname(tmpFileName)

    if not os.path.exists(dir):
        os.mkdir(dir)

    if args.version:
        print APP_DESC

    if args.append:
        append(tmpFileName, args.append)

    if args.edit:
        edit(tmpFileName, editor=conf['editor'])

    if args.post:
        post(tmpFileName,
             from_email=conf['from_email'],
             sender_nickname=conf['sender_nickname'],
             password=conf['sender_password'],
             to_email=conf['to_email'],
             cc=conf['cc'],
             host=conf['smtp_host'])

    if args.clean:
        clean(tmpFileName)

    if args.list:
        listContent(tmpFileName)
        baseOutput(conf)

    if args.restore:
        restore(confFileName)

    if args.backup:
        backup(confFileName)


def initializeArguments():
    parser = argparse.ArgumentParser(
        description='Tell your leader what you did this week')

    # define command line parameters
    parser.add_argument('-v', '--version',
                        action='store_true',
                        help='show the version information')
    parser.add_argument('-e', '--edit',
                        action='store_true',
                        help='open default editor for editing report')
    parser.add_argument('-a', '--append',
                        help='what did you do today?')
    parser.add_argument('-p', '--post',
                        action='store_true',
                        help='post the specified report to your leader e-mail')
    parser.add_argument('-l', '--list',
                        action='store_true',
                        help='list all the unpost report')
    parser.add_argument('-c', '--clean',
                        action='store_true',
                        help='clean current report')

    group = parser.add_mutually_exclusive_group()

    group.add_argument('-r', '--restore',
                       action='store_true',
                       help='restore lastest configuration file')
    group.add_argument('-b', '--backup',
                       action='store_true',
                       help='backup current configuration file')

    return parser.parse_args()


def baseOutput(conf):
    print '\r\n'

    if 'from_email' in conf and conf['from_email']:
        print 'From: %s<%s%s%s>' % (conf['sender_nickname'],
                                    Fore.GREEN,
                                    conf['from_email'],
                                    Fore.RESET)

    if 'to_email' in conf and conf['to_email']:
        print 'To: %s%s' % (Fore.GREEN, conf['to_email'])

    if 'cc' in conf and conf['cc']:
        print 'Cc: %s%s' % (Fore.GREEN, conf['cc'])


def loadConfig(configName):
    conf = {}

    if os.path.exists(configName):
        with open(configName, 'rb') as r:
            config = ConfigParser.ConfigParser()
            config.readfp(r)
            conf['editor'] = config.get('global', 'editor')
            conf['to_email'] = config.get('to', 'email')
            conf['cc'] = config.get('to', 'cc')
            conf['from_email'] = config.get('from', 'email')
            conf['sender_nickname'] = config.get('from', 'nickname')
            conf['sender_password'] = config.get('from', 'password')
            conf['smtp_host'] = config.get('SMTP', 'host')

    return defaults(conf, {'editor': 'vim'})


def append(fileName, text):
    with open(fileName, 'a') as w:
        w.write('- %s\r\n' % text)


def edit(fileName, **conf):
    os.system('%s %s' % (conf['editor'], fileName))


def listContent(fileName):
    if os.path.exists(fileName):
        with open(fileName, 'r') as r:
            line = r.readline().rstrip('\r\n')
            while line:
                print line
                line = r.readline().rstrip('\r\n')


def post(fileName, **conf):
    '''post email'''
    date = datetime.now().strftime('%Y-%m-%d')
    dir = os.path.dirname(fileName)
    content = ''

    if 'from_email' not in conf or not conf['from_email']:
        print Fore.RED + 'from_email is required'
        return

    if 'to_email' not in conf or not conf['to_email']:
        print Fore.RED + 'to_email is required'
        return

    if os.path.exists(fileName):
        with open(fileName, 'r') as r:
            content = r.read()

    if len(content) > 0:
        content = mistune.markdown(content, escape=True, hard_wrap=True)
        hFrom = Header(conf['sender_nickname'], 'utf-8')
        hFrom.append('<%s>\r\n' % conf['from_email'], 'utf-8')

        TO_ADDR = conf['to_email'].split(',')
        CC_ADDR = conf['cc'].split(',')

        hTo = ', '.join(TO_ADDR)
        hCc = ', '.join(CC_ADDR)

        msg = MIMEText(content, 'html', 'utf-8')
        msg['Subject'] = u'工作周报 %s\r\n' % date
        msg['From'] = hFrom
        msg['To'] = hTo
        msg['Cc'] = hCc

        smtp = smtplib.SMTP(conf['host'])
        smtp.login(conf['from_email'], conf['password'])
        smtp.sendmail(conf['from_email'],
                      TO_ADDR + CC_ADDR,
                      msg.as_string())
        smtp.close()

        os.rename(fileName, os.path.join(dir, '%s.rp' % date))

        print Fore.GREEN + 'Send successfully'
    else:
        print 'Nothing to send'


def clean(fileName):
    if os.path.exists(fileName):
        os.remove(fileName)


def restore(fileName):
    backupFile = '%s.bak' % fileName
    if os.path.exists(backupFile):
        shutil.copyfile(backupFile, fileName)
        print Fore.GREEN + 'Restore successfully'
    else:
        print Fore.RED + 'Backup configuration is not exisits'


def backup(fileName):
    if os.path.exists(fileName):
        shutil.copyfile(fileName, '%s.bak' % fileName)
        print Fore.GREEN + 'Backup successfully'

if __name__ == '__main__':
    main()
