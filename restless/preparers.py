class Preparer(object):
    """
    A plain preparation object which just passes through data.

    It also is relevant as the protocol subclasses should implement to work with
    Restless.
    """
    def __init__(self):
        super(Preparer, self).__init__()

    def prepare(self, data):
        """
        Handles actually transforming the data.

        By default, this does nothing & simply returns the data passed to it.
        """
        return data


class FieldsPreparer(Preparer):
    """
    A more complex preparation object, this will return a given set of fields.

    This takes a ``fields`` parameter, which should be a dictionary of
    keys (fieldnames to expose to the user) & values (a dotted lookup path to
    the desired attribute/key on the object).

    Example::

        preparer = FieldsPreparer(fields={
            # ``user`` is the key the client will see.
            # ``author.pk`` is the dotted path lookup ``FieldsPreparer``
            # will traverse on the data to return a value.
            'user': 'author.pk',
        })

    """
    def __init__(self, fields):
        super(FieldsPreparer, self).__init__()
        self.fields = fields

    def prepare(self, data):
        """
        Handles transforming the provided data into the fielded data that should
        be exposed to the end user.

        Uses the ``lookup_data`` method to traverse dotted paths.

        Returns a dictionary of data as the response.
        """
        result = {}

        if not self.fields:
            # No fields specified. Serialize everything.
            return data

        for fieldname, lookup in self.fields.items():
            if isinstance(lookup, SubPreparer):
                result[fieldname] = lookup.prepare(data)
            else:
                result[fieldname] = self.lookup_data(lookup, data)

        return result

    def lookup_data(self, lookup, data):
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

        if callable(getattr(data, 'keys', None)) and hasattr(data, '__getitem__'):
            # Dictionary enough for us.
            value = data[part]
        elif data is not None:
            # Assume it's an object.
            value = getattr(data, part)

        # Call if it's callable except if it's a Django DB manager instance
        #   We check if is a manager by checking the db_manager (duck typing)
        if callable(value) and not hasattr(value, 'db_manager'):
            value = value()

        if not remaining_lookup:
            return value

        # There's more to lookup, so dive in recursively.
        return self.lookup_data(remaining_lookup, value)


class SubPreparer(FieldsPreparer):
    """
    A preparation class designed to be used within other preparers.

    This is primary to enable deeply-nested structures, allowing you
    to compose/share definitions as well. Typical usage consists of creating
    a configured instance of a FieldsPreparer, then use a `SubPreparer` to
    pull it in.

    Example::

        # First, define the nested fields you'd like to expose.
        author_preparer = FieldsPreparer(fields={
            'id': 'pk',
            'username': 'username',
            'name': 'get_full_name',
        })
        # Then, in the main preparer, pull them in using `SubPreparer`.
        preparer = FieldsPreparer(fields={
            'author': SubPreparer('user', author_preparer),
            # Other fields can come before/follow as normal.
            'content': 'post',
            'created': 'created_at',
        })

    """
    def __init__(self, lookup, preparer):
        self.lookup = lookup
        self.preparer = preparer

    def get_inner_data(self, data):
        """
        Used internally so that the correct data is extracted out of the
        broader dataset, allowing the preparer being called to deal with just
        the expected subset.
        """
        return self.lookup_data(self.lookup, data)

    def prepare(self, data):
        """
        Handles passing the data to the configured preparer.

        Uses the ``get_inner_data`` method to provide the correct subset of
        the data.

        Returns a dictionary of data as the response.
        """
        return self.preparer.prepare(self.get_inner_data(data))


class CollectionSubPreparer(SubPreparer):
    """
    A preparation class designed to handle collections of data.

    This is useful in the case where you have a 1-to-many or many-to-many
    relationship of data to expose as part of the parent data.

    Example::

        # First, set up a preparer that handles the data for each thing in
        # the broader collection.
        comment_preparer = FieldsPreparer(fields={
            'comment': 'comment_text',
            'created': 'created',
        })
        # Then use it with the ``CollectionSubPreparer`` to create a list
        # of prepared sub items.
        preparer = FieldsPreparer(fields={
            # A normal blog post field.
            'post': 'post_text',
            # All the comments on the post.
            'comments': CollectionSubPreparer('comments.all', comment_preparer),
        })

    """
    def prepare(self, data):
        """
        Handles passing each item in the collection data to the configured
        subpreparer.

        Uses a loop and the ``get_inner_data`` method to provide the correct
        item of the data.

        Returns a list of data as the response.
        """
        result = []

        for item in self.get_inner_data(data):
            result.append(self.preparer.prepare(item))

        return result
