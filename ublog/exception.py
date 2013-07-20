
# -*- coding:utf-8 -*-

class RequestError(Exception):
    pass

class RemoteError(RequestError):
    pass

class LocalError(RequestError):
    pass

class NumberError(RemoteError):
    pass

class UnknownError(RemoteError):
    pass

