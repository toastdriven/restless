import datetime
import decimal

try:
    import json
except ImportError:
    import simplejson as json


def lookup_data(lookup, data):
    """
    Given a lookup string, attempts to descend through nested data looking for
    the value.

    Can work with either dictionary-alikes or objects (or any combination of
    those).

    Lookups should be a string. If it is a dotted path, it will be split on
    ``.`` & it will traverse through to find the final value. If not, it will
    simply attempt to find either a key or attribute of that name & return it.

    Example::

        >>> data = {
        ...     'type': 'message',
        ...     'greeting': {
        ...         'en': 'hello',
        ...         'fr': 'bonjour',
        ...         'es': 'hola',
        ...     },
        ...     'person': Person(
        ...         name='daniel'
        ...     )
        ... }
        >>> lookup_data('type', data)
        'message'
        >>> lookup_data('greeting.en', data)
        'hello'
        >>> lookup_data('person.name', data)
        'daniel'

    """
    value = data
    parts = lookup.split('.')

    if not parts or not parts[0]:
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
    """
    A JSON encoder that allows for more common Python data types.

    In addition to the defaults handled by ``json``, this also supports:

        * ``datetime.datetime``
        * ``datetime.date``
        * ``datetime.time``
        * ``decimal.Decimal``

    """
    def default(self, data):
        if isinstance(data, (datetime.datetime, datetime.date, datetime.time)):
            return data.isoformat()
        elif isinstance(data, decimal.Decimal):
            return str(data)
        else:
            return super(MoreTypesJSONEncoder, self).default(data)
