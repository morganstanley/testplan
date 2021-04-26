
__all__ = ['b', 'text', 'basestring_', 'coerce_text', 'iteritems']

text = str
basestring_ = (bytes, str)


def b(s):
    if isinstance(s, str):
        return s.encode('latin1')
    return bytes(s)


def coerce_text(v):
    if not isinstance(v, basestring_):
        if hasattr(v, '__str__'):
            return str(v)
        else:
            return bytes(v)
    return v


def iteritems(d, **kw):
    return iter(d.items(**kw))
