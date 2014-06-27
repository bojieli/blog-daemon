
# -*- coding:utf-8 -*-

import os.path

ALLOW_PATH = (
    "/srv/blog"
    )

_p = dict()
_p['action.http.timeout']		= 30
_p['action.http.max_response_size']	= 10485760 # 10M
_p['path.tmp']			= '/srv/blog/tmp'
_p['path.wp.source']		= '/srv/blog/wp-tobecopied'
_p['path.base']			= '/srv/blog/base'
_p['path.user']			= lambda appname:		os.path.join(get_param('path.base'), appname)
_p['path.user.wp.config']	= lambda appname:		os.path.join(get_param('path.base'), appname, 'wp-config.php')
_p['path.user.plugin.base']	= lambda appname:		os.path.join(get_param('path.user', appname=appname), 'wp-content/plugins')
_p['path.user.plugin']		= lambda appname, plugin:	os.path.join(get_param('path.user.plugin.base', appname=appname), plugin)
_p['path.user.theme.base']	= lambda appname:		os.path.join(get_param('path.user', appname=appname), 'wp-content/themes')
_p['path.user.theme']		= lambda appname, theme:	os.path.join(get_param('path.user.theme.base', appname=appname), theme)
_p['path.user.upload']		= lambda appname:		os.path.join(get_param('path.user', appname=appname), 'wp-content/uploads')
_p['path.nginx.config']         = '/etc/nginx/autogen-conf-blog'
_p['url.plugin.base']		= 'http://downloads.wordpress.org/plugin/'
_p['url.theme.base']		= 'http://wordpress.org/extend/themes/download/'
_p['action.sendmail.from']	= 'noreply@blog.ustc.edu.cn'
_p['action.sendmail.server'] = 'localhost'
_p['async.post.url']		= 'http://127.0.0.1:10000/callback.php'

_p['script.base']               = '/opt/ustcblog/blog-daemon/scripts'
_p['script.nginx.reload']       = _p['script.base'] + '/safe-reload-nginx'
_p['script.sslkey.install']     = _p['script.base'] + '/install-ssl-key'

_p['handler.worker-pool-async.size']	= 10

_p['logger.request']		= '/tmp/log/request.log'
_p['logger.exception']		= '/tmp/log/exception.log'
    
def get_param(param, **kwargs):
    if param in _p:
        p = _p[param]
    else:
        raise Exception("bad param name " + str(param))

    if callable(p):
        p = p(**kwargs)

    assert isinstance(p, (int, basestring)), Exception("bad param content of " + str(param))

    if isinstance(p, basestring):
        if p.startswith('path.'):
            assert os.path.isabs(p)

            allowed = False
            for al in ALLOW_PATH:
                cf = os.path.commonprefix([p, al])
                if cf == al:
                    allowed = True
                    break
            assert allowed

    return p


