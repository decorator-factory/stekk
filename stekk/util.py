# from Stackoverflow

import functools

class StrWrapper:
    def __init__(self, repr_, func):
        self._repr = repr_
        self._func = func
        functools.update_wrapper(self, func)

    def __call__(self, *args, **kwargs):
        return self._func(*args, **kwargs)

    def __str__(self):
        return self._repr(self._func)

def withrepr(strfun):
    def _wrap(func):
        return StrWrapper(strfun, func)
    return _wrap

