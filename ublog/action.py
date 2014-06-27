
# -*- coding:utf-8 -*-

from ublog.params import get_param
import ublog.exception as ue
import ublog.request
import ublog.utils

import sys
import os
import os.path
import io
import errno
import stat
import traceback

import random
import string

import urllib
import urllib2
import urlparse
import httplib
import subprocess

import re
import shutil
import zipfile

from email.mime.text import MIMEText
import email.utils
import smtplib

_action_execute_map = dict()

def default_action(request):
    raise ue.UnknownError
    

def add_action(action, executor):
    assert isinstance(action, str)
    assert action not in _action_execute_map

    _action_execute_map[action] = executor

def daction(name):
    def action_adder(executor):
        add_action(name, executor)
    return action_adder

class Action(object):

    def __init__(self, action):
        self._action = action

    def __call__(self, request):
        try:
            result = self._action(request)
        except:
            traceback.print_exc()
            result = '*Exception Raised'

        if result is None:
            result = dict(status = '0')

        if isinstance(result, int):
            result = dict(status = str(result))

        if isinstance(result, dict):
            try:
                result = str(ublog.request.StructedDict(result))
            except:
                result = '*Bad Result'

        if not isinstance(result, str):
            result = '*Unknown Result'
        return result
    
def _get_action(action):
    assert isinstance(action, str)
    if action in _action_execute_map:
        return _action_execute_map[action]
    return default_action

def get_action(action):
    return Action(_get_action(action))


@daction('ping')
def ping(request):
    return 'pong'


def _http_request(url, method, post_data=None):
    r = urlparse.urlparse(url)
    assert r.scheme == 'http'
    # assert not r.port

    assert method == 'GET' and post_data == None or method == 'POST'
    if method == 'POST' and post_data == None:
        post_data = []

    try:
        uc = urllib2.urlopen( url, post_data, get_param('action.http.timeout') )
        data = uc.read(ublog.params.get_param('action.http.max_response_size'))
        if uc.read(1) != '':
            raise ue.UnknownError("response too long")        
    except urllib2.HTTPError as e:
        return {'status': str(e.code), 'data': ''}
    finally:
        try:
            uc.close()
        except:
            pass
    return {'status': '200', 'data': data}

@daction('http-get')
def http_get(request):
    url = request.args['url'] # KeyError
    return _http_request(url, 'GET')

@daction('http-post')
def http_post(request):
    url = request.args['url'] # KeyError
    try:
        request.args['body']
    except:
        return _http_request(url, 'POST')
    return _http_request(url, 'POST', request.args['body'])

@daction('access-log')
def access_log(request):
    assert request.appname != None
    int(request.args['exec-time'])
    int(request.args['query-num'])

@daction('install-blog-filesystem')
def install_blog_filesystem(request):
    appname = request.appname
    assert appname != None

    appbase = ublog.params.get_param('path.user', appname=appname)
    wpsrc   = ublog.params.get_param('path.wp.source')

    subprocess.check_call(['rm', '-rf', '--', appbase])
    subprocess.check_call(['cp', '-rfP', '--', wpsrc, appbase])

    upload = get_param('path.user.upload', appname=appname)

    mode = stat.S_IRWXU | stat.S_IRWXG | stat.S_IROTH | stat.S_IXOTH
    try:
        os.mkdir(upload, mode)
    except:
        pass
    os.chmod(upload, mode)

    keys = (
        'AUTH_KEY',
        'SECURE_AUTH_KEY',
        'LOGGED_IN_KEY',
        'NONCE_KEY',
        'AUTH_SALT',
        'SECURE_AUTH_SALT',
        'LOGGED_IN_SALT',
        'NONCE_SALT',
        )
    maxlen = max([len(k) for k in keys])
    keyscomma = [ "'" + k + "'," + ' '*(maxlen-len(k)) for k in keys]
    s = "<?php\n" + ''.join(["define({0} '{1}');\n".format(kc, ublog.utils.random_string(64)) for kc in keyscomma]) + "?>\n"
    with io.open(get_param('path.user.wp.config', appname=appname), 'wb') as f:
        f.write(s)
        

PLUGIN_NAME_RE = re.compile('^[-0-9a-zA-Z._]+$')
PLUGIN_FILENAME_RE = re.compile('^[-0-9a-zA-Z._]+\.zip$')
@daction('install-plugin')
def install_plugin(request):
    appname = request.appname
    assert appname != None

    plugin_name = request.args['plugin-name']
    assert PLUGIN_NAME_RE.match(plugin_name)
    plugin_filename = request.args['remote-filename']
    assert PLUGIN_FILENAME_RE.match(plugin_filename)

    url = get_param('url.plugin.base') + plugin_filename
    tmpfname = os.path.join(get_param('path.tmp'), ublog.utils.random_string(64)+'.'+plugin_filename)

    plugin_base = get_param('path.user.plugin.base', appname=appname)

    u = urllib2.urlopen(url)
    try:
        with io.open(tmpfname, 'wb') as f:
            f.write(u.read())
        zf = zipfile.ZipFile(tmpfname)
        try:
            for name in zf.namelist():
                assert name.startswith(plugin_name+'/')
                zf.extract(name, plugin_base)
        except:
            shutil.rmtree(plugin_base)
            raise
        finally:
            zf.close()
    finally:
        u.close()
        os.unlink(tmpfname)

@daction('remove-plugin')
def remove_plugin(request):
    appname = request.appname
    assert appname != None

    plugin_name = request.args['plugin-name']
    assert PLUGIN_NAME_RE.match(plugin_name)

    plugin_path = ublog.params.get_param('path.user.plugin', appname=appname, plugin=plugin_name)

    shutil.rmtree(plugin_path)


THEME_NAME_RE = PLUGIN_NAME_RE
THEME_FILENAME_RE = PLUGIN_FILENAME_RE
@daction('install-theme')
def install_theme(request):
    appname = request.appname
    assert appname != None

    theme_name = request.args['theme-name']
    assert PLUGIN_NAME_RE.match(theme_name)
    theme_filename = request.args['remote-filename']
    assert PLUGIN_FILENAME_RE.match(theme_filename)

    url = get_param('url.theme.base') + theme_filename
    tmpfname = os.path.join(get_param('path.tmp'), ublog.utils.random_string(64)+'.'+theme_filename)

    theme_base = get_param('path.user.theme.base', appname=appname)

    u = urllib2.urlopen(url)
    try:
        with io.open(tmpfname, 'wb') as f:
            f.write(u.read())
        zf = zipfile.ZipFile(tmpfname)
        try:
            for name in zf.namelist():
                assert name.startswith(theme_name+'/')
                zf.extract(name, theme_base)
        except:
            shutil.rmtree(theme_base)
            raise
        finally:
            zf.close()
    finally:
        u.close()
        os.unlink(tmpfname)

@daction('remove-theme')
def remove_theme(request):
    appname = request.appname
    assert appname != None

    theme_name = request.args['theme-name']
    assert PLUGIN_NAME_RE.match(theme_name)

    theme_path = ublog.params.get_param('path.user.theme', appname=appname, theme=theme_name)

    shutil.rmtree(theme_path)


@daction('sendmail')
def sendmail(request):
    target  = request.args['target']

    subject = request.args['subject']
    if not isinstance(subject, unicode):
        subject = subject.decode('utf-8')
    content = request.args['content']
    if not isinstance(content, unicode):
        content = content.decode('utf-8')

    mail_from = get_param('action.sendmail.from')
    mail_to   = target

    msg = MIMEText(content, 'plain', 'utf-8')
    msg['From'] = mail_from
    msg['To']   = mail_to
    msg['Subject'] = subject
    msg['Date']    = email.utils.formatdate(localtime=True)

    server = smtplib.SMTP(get_param('action.sendmail.server'))
    server.sendmail(mail_from, [mail_to], msg.as_string())
    server.quit()
    
@daction('set-3rdparty-domain')
def set_3rdparty_domain(request):
    appname     = request.appname
    domain_name = request.args['domain']
    is_ssl      = bool(int(request.args['is_ssl']))
    if not re.search(r'^[a-z\d-]{,63}$', appname):
        return 1
    if not re.search(r'^[a-z\d-]{,63}(\.[a-z\d-]{,63})+$', domain_name):
        return 2
    try:
        conf = open(get_param('path.nginx.config') + '/' + appname, 'w')
        if is_ssl:
            listen_443 = '''
            listen 443;
            listen [::]:443;
            include conf.d/redirect2https.inc;'''
            ssl_cert = '''
            ssl_certificate     /etc/nginx/blog-keys/{0}.crt;
            ssl_certificate_key /etc/nginx/blog-keys/{0}.key;'''.format(appname)
        else:
            listen_443 = ''
            ssl_cert = ''

        # warning: special chars '{' and '}' need to be escaped
        conf.write('''
        server {{
            listen 80;
            listen [::]:80;
            {2}

            server_name {1};
            
            {3}

            access_log /var/log/nginx/blog/access.log logverbose;
            error_log  /var/log/nginx/blog/error.log;

            location / {{
                proxy_pass $scheme://127.0.0.1;
                proxy_set_header Host            {0}.blog.ustc.edu.cn;
                proxy_set_header X-Original-Host $http_host;
            }}
        }}
        '''.format(appname, domain_name, listen_443, ssl_cert))
        conf.close()
    except Exception, e:
        print Exception, e
        return 3

    try:
        # os.system return value is (process return value << 8) 
        status = os.system('sudo ' + get_param('script.nginx.reload')) >> 8
        if status != 0:
            return 4
    except Exception, e:
	print Exception, e
        return 4
    return 0

@daction('install-ssl-key')
def install_ssl_key(request):
    appname     = request.appname
    domain_name = request.args['domain']
    if not re.search(r'^[a-z\d-]{,63}$', appname):
        return 1
    if not re.search(r'^[a-z\d-]{,63}(\.[a-z\d-]{,63})+$', domain_name):
        return 2
    try:
        status = os.system(get_param('script.sslkey.install') + ' ' + appname + ' ' + domain_name) >> 8
        if status != 0:
            return status
    except Exception, e:
	print Exception, e
        return 3
    return 0

