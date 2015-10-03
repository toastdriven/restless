import datetime
import decimal
import traceback
import uuid

try:
    import json
except ImportError:
    import simplejson as json


class MoreTypesJSONEncoder(json.JSONEncoder):
    """
    A JSON encoder that allows for more common Python data types.

    In addition to the defaults handled by ``json``, this also supports:

        * ``datetime.datetime``
        * ``datetime.date``
        * ``datetime.time``
        * ``decimal.Decimal``
        * ``uuid.UUID``

    """
    def default(self, data):
        if isinstance(data, (datetime.datetime, datetime.date, datetime.time)):
            return data.isoformat()
        elif isinstance(data, decimal.Decimal) or isinstance(data, uuid.UUID):
            return str(data)
        else:
            return super(MoreTypesJSONEncoder, self).default(data)


def format_traceback(exc_info):
    stack = traceback.format_stack()
    stack = stack[:-2]
    stack.extend(traceback.format_tb(exc_info[2]))
    stack.extend(traceback.format_exception_only(exc_info[0], exc_info[1]))
    stack_str = "Traceback (most recent call last):\n"
    stack_str += "".join(stack)
    # Remove the last \n
    stack_str = stack_str[:-1]
    return stack_str
