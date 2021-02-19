"""Utils for FIX."""

import datetime

DATEFORMAT = "%Y%m%d-%H:%M:%S.%f"


def utc_timestamp():
    """
    :return: a UTCTimestamp (see FIX spec)
    :rtype: ``str``
    """
    return datetime.datetime.utcnow().strftime(DATEFORMAT)
