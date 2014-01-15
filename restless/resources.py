import six

from .constants import OK, CREATED, ACCEPTED, NO_CONTENT
from .exceptions import MethodNotImplemented, Unauthorized
from .utils import json, lookup_data, MoreTypesJSONEncoder


class Resource(object):
    """
    Defines a RESTful resource.

    Users are expected to subclass this object & implement a handful of methods:

    * ``list``
    * ``detail``
    * ``create`` (requires authentication)
    * ``update`` (requires authentication)
    * ``delete`` (requires authentication)

    Additionally, the user may choose to implement:

    * ``create_detail`` (requires authentication)
    * ``update_list`` (requires authentication)
    * ``delete_list`` (requires authentication)

    Users may also wish to define a ``fields`` attribute on the class. By
    providing a dictionary of output names mapped to a dotted lookup path, you
    can control the serialized output.

    Users may also choose to override the ``status_map`` and/or ``http_methods``
    on the class. These respectively control the HTTP status codes returned by
    the views and the way views are looked up (based on HTTP method & endpoint).
    """
    fields = None
    status_map = {
        'list': OK,
        'detail': OK,
        'create': CREATED,
        'update': ACCEPTED,
        'delete': NO_CONTENT,
        'update_list': ACCEPTED,
        'create_detail': CREATED,
        'delete_list': NO_CONTENT,
    }
    http_methods = {
        'list': {
            'GET': 'list',
            'POST': 'create',
            'PUT': 'update_list',
            'DELETE': 'delete_list',
        },
        'detail': {
            'GET': 'detail',
            'POST': 'create_detail',
            'PUT': 'update',
            'DELETE': 'delete',
        }
    }

    def __init__(self, *args, **kwargs):
        self.init_args = args
        self.init_kwargs = kwargs
        self.request = None
        self.data = None
        self.status = 200

    @classmethod
    def as_list(cls, *init_args, **init_kwargs):
        """
        Used for hooking up the actual list-style endpoints, this returns a
        wrapper function that creates a new instance of the resource class &
        calls the correct view method for it.

        :param init_args: (Optional) Positional params to be persisted along
            for instantiating the class itself.

        :param init_kwargs: (Optional) Keyword params to be persisted along
            for instantiating the class itself.

        :returns: View function
        """
        def _wrapper(request, *args, **kwargs):
            # Make a new instance so that no state potentially leaks between
            # instances.
            inst = cls(*init_args, **init_kwargs)
            inst.request = request
            return inst.handle('list', *args, **kwargs)

        return _wrapper

    @classmethod
    def as_detail(cls, *init_args, **init_kwargs):
        """
        Used for hooking up the actual detail-style endpoints, this returns a
        wrapper function that creates a new instance of the resource class &
        calls the correct view method for it.

        :param init_args: (Optional) Positional params to be persisted along
            for instantiating the class itself.

        :param init_kwargs: (Optional) Keyword params to be persisted along
            for instantiating the class itself.

        :returns: View function
        """
        def _wrapper(request, *args, **kwargs):
            # Make a new instance so that no state potentially leaks between
            # instances.
            inst = cls(*init_args, **init_kwargs)
            inst.request = request
            return inst.handle('detail', *args, **kwargs)

        return _wrapper

    def request_method(self):
        """
        Returns the HTTP method for the current request.

        The default implementation is Django-specific, so if you're integrating
        with a new web framework, you'll need to override this method within
        your subclass.

        :returns: The HTTP method in uppercase
        :rtype: string
        """
        # By default, Django-esque.
        return self.request.method.upper()

    def request_body(self):
        """
        Returns the body of the current request.

        Useful for deserializing the content the user sent (typically JSON).

        The default implementation is Django-specific, so if you're integrating
        with a new web framework, you'll need to override this method within
        your subclass.

        :returns: The body of the request
        :rtype: string
        """
        # By default, Django-esque.
        return self.request.body

    def build_response(self, data, status=200):
        """
        Given some data, generates an HTTP response.

        The default implementation is Django-specific, so if you're integrating
        with a new web framework, you'll need to override this method within
        your subclass.

        :param data: The body of the response to send
        :type data: string

        :param status: (Optional) The status code to respond with. Default is
            ``200``
        :type status: integer

        :returns: A response object
        """
        # TODO: Remove the Django.
        #       This should be plain old WSGI by default, if possible.
        # By default, Django-esque.
        from django.http import HttpResponse
        resp = HttpResponse(data, content_type='application/json')
        resp.status_code = status
        return resp

    def build_error(self, err):
        """
        When an exception is encountered, this generates a JSON error message
        for display to the user.

        :param err: The exception seen. The message is exposed to the user, so
            beware of sensitive data leaking.
        :type err: Exception

        :returns: A response object
        """
        data = json.dumps({
            'error': six.text_type(err),
        })
        status = getattr(err, 'status', 500)
        return self.build_response(data, status=status)

    def is_debug(self):
        """
        Controls whether or not the resource is in a debug environment.

        If so, exceptions will be reraised instead of returning a serialized
        response.

        The default implementation simply returns ``False``, so if you're
        integrating with a new web framework, you'll need to override this
        method within your subclass.

        :returns: If the resource is in a debug environment
        :rtype: boolean
        """
        return False

    def handle(self, endpoint, *args, **kwargs):
        """
        A convenient dispatching method, this centralized some of the common
        flow of the views.

        This wraps/calls the methods the user defines (``list/detail/create``
        etc.), allowing the user to ignore the
        authentication/deserialization/serialization/response & just focus on
        their data/interactions.

        :param endpoint: The style of URI call (typically either ``list`` or
            ``detail``).
        :type endpoint: string

        :param args: (Optional) Any positional URI parameter data is passed
            along here. Somewhat framework/URL-specific.

        :param kwargs: (Optional) Any keyword/named URI parameter data is
            passed along here. Somewhat framework/URL-specific.

        :returns: A response object
        """
        method = self.request_method()

        try:
            # Use ``.get()`` so we can also dodge potentially incorrect
            # ``endpoint`` errors as well.
            if not method in self.http_methods.get(endpoint, {}):
                raise MethodNotImplemented(
                    "Unsupported method '{0}' for {1} endpoint.".format(
                        method,
                        endpoint
                    )
                )

            if not self.is_authenticated():
                raise Unauthorized()

            body = self.request_body()
            self.data = self.deserialize(method, endpoint, body)
            view_method = getattr(self, self.http_methods[endpoint][method])
            data = view_method(*args, **kwargs)
            serialized = self.serialize(method, endpoint, data)
        except Exception as err:
            if self.is_debug():
                raise

            return self.build_error(err)

        status = self.status_map.get(self.http_methods[endpoint][method], OK)
        return self.build_response(serialized, status=status)

    def raw_deserialize(self, body):
        """
        The low-level deserialization.

        Underpins ``deserialize``, ``deserialize_list`` &
        ``deserialize_detail``.

        Has no built-in smarts, simply loads the JSON.

        :param body: The body of the current request
        :type body: string

        :returns: The deserialized data
        :rtype: ``list`` or ``dict``
        """
        return json.loads(body)

    def raw_serialize(self, data):
        """
        The low-level serialization.

        Underpins ``serialize``, ``serialize_list`` &
        ``serialize_detail``.

        Has no built-in smarts, simply dumps the JSON.

        :param data: The body for the response
        :type data: string

        :returns: A serialized version of the data
        :rtype: string
        """
        return json.dumps(data, cls=MoreTypesJSONEncoder)

    def deserialize(self, method, endpoint, body):
        """
        A convenience method for deserializing the body of a request.

        If called on a list-style endpoint, this calls ``deserialize_list``.
        Otherwise, it will call ``deserialize_detail``.

        :param method: The HTTP method of the current request
        :type method: string

        :param endpoint: The endpoint style (``list`` or ``detail``)
        :type endpoint: string

        :param body: The body of the current request
        :type body: string

        :returns: The deserialized data
        :rtype: ``list`` or ``dict``
        """
        if endpoint == 'list':
            return self.deserialize_list(body)

        return self.deserialize_detail(body)

    def deserialize_list(self, body):
        """
        Given a string of text, deserializes a (presumed) list out of the body.

        :param body: The body of the current request
        :type body: string

        :returns: The deserialized body or an empty ``list``
        """
        if body:
            return self.raw_deserialize(body)

        return []

    def deserialize_detail(self, body):
        """
        Given a string of text, deserializes a (presumed) object out of the body.

        :param body: The body of the current request
        :type body: string

        :returns: The deserialized body or an empty ``dict``
        """
        if body:
            return self.raw_deserialize(body)

        return {}

    def serialize(self, method, endpoint, data):
        """
        A convenience method for serializing data for a response.

        If called on a list-style endpoint, this calls ``serialize_list``.
        Otherwise, it will call ``serialize_detail``.

        :param method: The HTTP method of the current request
        :type method: string

        :param endpoint: The endpoint style (``list`` or ``detail``)
        :type endpoint: string

        :param data: The body for the response
        :type data: string

        :returns: A serialized version of the data
        :rtype: string
        """
        if endpoint == 'list':
            # Create is a special-case, because you POST it to the collection,
            # not to a detail.
            if method == 'POST':
                return self.serialize_detail(data)

            return self.serialize_list(data)
        return self.serialize_detail(data)

    def serialize_list(self, data):
        """
        Given a collection of data (``objects`` or ``dicts``), serializes them.

        This will call ``prepare`` for each item, to optionally reshape the
        output.

        :param data: The collection of items to serialize
        :type data: list or iterable

        :returns: The serialized body
        :rtype: string
        """
        if data is None:
            return ''

        prepped_data = [self.prepare(item) for item in data]
        final_data = self.wrap_list_response(prepped_data)
        return self.raw_serialize(final_data)

    def serialize_detail(self, data):
        """
        Given a single item (``object`` or ``dict``), serializes it.

        This will call ``prepare`` on the item, to optionally reshape the
        output.

        :param data: The item to serialize
        :type data: object or dict

        :returns: The serialized body
        :rtype: string
        """
        if data is None:
            return ''

        final_data = self.prepare(data)
        return self.raw_serialize(final_data)

    def prepare(self, data):
        """
        Given an item (``object`` or ``dict``), this will potentially go through
        & reshape the output based on ``self.fields``.

        If ``self.fields`` is empty or ``None``, the entire thing will be
        returned.

        If ``self.fields`` is present/populated, this will use the lookup to
        extract data & shape the resulting output match the keys of
        ``self.fields``.

        :param data: An item to prepare for serialization
        :type data: object or dict

        :returns: A potentially reshaped dict
        :rtype: dict
        """
        result = {}

        if not self.fields:
            # No fields specified. Serialize everything.
            return data

        for fieldname, lookup in self.fields.items():
            result[fieldname] = lookup_data(lookup, data)

        return result

    def wrap_list_response(self, data):
        """
        Takes a list of data & wraps it in a dictionary (within the ``objects``
        key).

        For security in JSON responses, it's better to wrap the list results in
        an ``object`` (due to the way the ``Array`` constructor can be attacked
        in Javascript). See http://haacked.com/archive/2009/06/25/json-hijacking.aspx/
        & similar for details.

        Overridable to allow for modifying the key names, adding data (or just
        insecurely return a plain old list if that's your thing).

        :param data: A list of data about to be serialized
        :type data: list

        :returns: A wrapping dict
        :rtype: dict
        """
        return {
            "objects": data
        }

    def is_authenticated(self):
        """
        A simple hook method for controlling whether a request is authenticated
        to continue.

        By default, we only allow the safe ``GET`` methods. All others are
        denied.

        :returns: Whether the request is authenticated or not.
        :rtype: boolean
        """
        if self.request_method() == 'GET':
            return True

        return False

    # Common methods the user should implement.

    def list(self, *args, **kwargs):
        """
        Returns the data for a GET on a list-style endpoint.

        **MUST BE OVERRIDDEN BY THE USER** - By default, this returns
        ``MethodNotImplemented``.

        :returns: A collection of data
        :rtype: list or iterable
        """
        raise MethodNotImplemented()

    def detail(self, *args, **kwargs):
        """
        Returns the data for a GET on a detail-style endpoint.

        **MUST BE OVERRIDDEN BY THE USER** - By default, this returns
        ``MethodNotImplemented``.

        :returns: An item
        :rtype: object or dict
        """
        raise MethodNotImplemented()

    def create(self, *args, **kwargs):
        """
        Allows for creating data via a POST on a list-style endpoint.

        **MUST BE OVERRIDDEN BY THE USER** - By default, this returns
        ``MethodNotImplemented``.

        :returns: May return the created item or ``None``
        """
        raise MethodNotImplemented()

    def update(self, *args, **kwargs):
        """
        Updates existing data for a PUT on a detail-style endpoint.

        **MUST BE OVERRIDDEN BY THE USER** - By default, this returns
        ``MethodNotImplemented``.

        :returns: May return the updated item or ``None``
        """
        raise MethodNotImplemented()

    def delete(self, *args, **kwargs):
        """
        Deletes data for a DELETE on a detail-style endpoint.

        **MUST BE OVERRIDDEN BY THE USER** - By default, this returns
        ``MethodNotImplemented``.

        :returns: ``None``
        """
        raise MethodNotImplemented()

    # Uncommon methods the user should implement.
    # These have intentionally uglier method names, which reflects just how
    # much harder they are to get right.

    def update_list(self, *args, **kwargs):
        """
        Updates the entire collection for a PUT on a list-style endpoint.

        Uncommonly implemented due to the complexity & (varying) busines-logic
        involved.

        **MUST BE OVERRIDDEN BY THE USER** - By default, this returns
        ``MethodNotImplemented``.

        :returns: A collection of data
        :rtype: list or iterable
        """
        raise MethodNotImplemented()

    def create_detail(self, *args, **kwargs):
        """
        Creates a subcollection of data for a POST on a detail-style endpoint.

        Uncommonly implemented due to the rarity of having nested collections.

        **MUST BE OVERRIDDEN BY THE USER** - By default, this returns
        ``MethodNotImplemented``.

        :returns: A collection of data
        :rtype: list or iterable
        """
        raise MethodNotImplemented()

    def delete_list(self, *args, **kwargs):
        """
        Deletes *ALL* data in the collection for a DELETE on a list-style
        endpoint.

        Uncommonly implemented due to potential of trashing large datasets.
        Implement with care.

        **MUST BE OVERRIDDEN BY THE USER** - By default, this returns
        ``MethodNotImplemented``.

        :returns: ``None``
        """
        raise MethodNotImplemented()
