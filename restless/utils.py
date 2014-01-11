import datetime
import decimal

try:
    import json
except ImportError:
    import simplejson as json


def lookup_data(lookup, data):
    value = data
    parts = lookup.split('.')

    if not parts:
        return value

    part = parts[0]
    remaining_lookup = '.'.join(parts[1:])

    if hasattr(data, 'keys') and hasattr(data, '__getitem__'):
        # Dictionary enough for us.
        value = data[part]
    else:
        # Assume it's an object.
        value = getattr(data, part)

    if not remaining_lookup:
        return value

    # There's more to lookup, so dive in recursively.
    return lookup_data(remaining_lookup, value)


class MoreTypesJSONEncoder(json.JSONEncoder):
    def default(self, data):
        if isinstance(data, (datetime.datetime, datetime.date, datetime.time)):
            return data.isoformat()
        elif isinstance(data, decimal.Decimal):
            return str(data)
        else:
            return super(MoreTypesJSONEncoder, self).default(data)
