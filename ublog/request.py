# -*- coding:utf-8 -*-

import string
import base64
import urllib


ASCII_CHARSET  = ''.join([ chr(x) for x in range(128)  ])
KEY_CHARSET    = string.ascii_letters + string.digits + '._-'
LINE_SEPARTER  = "\n"
FIELD_SEPARTER = ':'
PLAIN_CHARSET  = string.ascii_letters + string.digits + '._-'

APPID_CHARSET  = string.digits
APPNAME_CHARSET  = string.ascii_letters + string.digits + '-'





        

class StructedDict(object):

    def __init__(self, d=None):
        if d == None:
            d = dict()
        self._dict = d

    @classmethod
    def validate_key(cls, key):
        s = key.strip(KEY_CHARSET)
        assert s == "", ValueError
        
    @classmethod
    def parse_line(cls, line):
        assert isinstance(line, str), TypeError
        
        sp = line.split(FIELD_SEPARTER, 3)
        if len(sp) != 3:
            raise ValueError
        key, enc, e_val = sp
        cls.validate_key(key)

        try:
            if enc == 'p':
                assert e_val.strip(PLAIN_CHARSET) == ''
                val = e_val
            elif enc == 'b':
                val = base64.standard_b64decode(e_val)
            elif enc == 'u':
                val = urllib.unquote_plus(e_val)
            else:
                raise ValueError
        except:
            raise ValueError

        return (key, val)

    @classmethod
    def encode_pair(cls, key, value):
        cls.validate_key(key)
        assert isinstance(value, str), TypeError
        return key + ':b:' + base64.standard_b64encode(value)

    def add_line(self, line):
        k,v = self.parse_line(line)
        assert k not in self._dict, ValueError
        self._dict[k] = v

    def add_lines(self, lines):
        for line in lines:
            self.add_line(line)

    def get_dict(self):
        return self._dict

    def __getitem__(self, k):
        return self._dict.k
    def __setitem__(self, k, v):
        self._dict[k] = v
    def __delitem__(self, k):
        del self._dict[k]

    def __str__(self):
        buf = ''
        for k,v in self._dict.items():
            buf = buf + self.encode_pair(k,v) + '\n'
        return buf

    @classmethod
    def lines_to_dict(cls, lines):
        ins = cls()
        ins.add_lines(lines)
        return ins.get_dict()

    

class StructedRequest(object):

    MAX_LINES = 50

    def __init__(self, request_data):
        assert isinstance(request_data, str), TypeError
        self._request_data = request_data

        s = self.request_data.split(LINE_SEPARTER, self.MAX_LINES)
        assert len(s) < self.MAX_LINES, ValueError

        i = s.index("")

        head  = StructedDict.lines_to_dict(s[:i])
        args  = StructedDict.lines_to_dict(s[i+1:-1])

        self._head  = head
        self._args  = args

        self.validate_head()


    head_key_need  = ['action', 'method']
    head_key_allow = head_key_need + ['appname', 'appid']
    def validate_head(self):
        for k in self.head_key_need:
            assert k in self._head, ValueError
        for k in self._head:
            assert k in k in self.head_key_allow, ValueError
        if 'appname' in self._head:
            appname = self._head['appname']
            assert len(appname) > 0 and appname.strip(APPNAME_CHARSET) == "", ValueError
        if 'appid' in self._head:
            appid = self._head['appid']
            assert len(appid) > 0 and appid.strip(APPID_CHARSET) == "", ValueError

    @property
    def request_data(self):
        return self._request_data

    @property
    def head(self):
        return self._head

    @property
    def args(self):
        return self._args
        
    @property
    def action(self):
        return self._head.get('action')

    @property
    def method(self):
        return self._head.get('method')

    @property
    def appid(self):
        return self._head.get('appid')

    @property
    def appname(self):
        return self._head.get('appname')
