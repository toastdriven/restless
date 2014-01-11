import six

from .constants import OK, CREATED, ACCEPTED, NO_CONTENT
from .exceptions import MethodNotImplemented
from .utils import json, lookup_data, MoreTypesJSONEncoder


class Resource(object):
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
        def _wrapper(request, *args, **kwargs):
            # Make a new instance so that no state potentially leaks between
            # instances.
            inst = cls(*init_args, **init_kwargs)
            inst.request = request
            return inst.handle('list', *args, **kwargs)

        return _wrapper

    @classmethod
    def as_detail(cls, *init_args, **init_kwargs):
        def _wrapper(request, *args, **kwargs):
            # Make a new instance so that no state potentially leaks between
            # instances.
            inst = cls(*init_args, **init_kwargs)
            inst.request = request
            return inst.handle('detail', *args, **kwargs)

        return _wrapper

    def request_method(self):
        # By default, Django-esque.
        return self.request.method.upper()

    def build_response(self, data, status=200):
        # FIXME: Remove the Django.
        #        This should be plain old WSGI by default if possible
        # By default, Django-esque.
        from django.http import HttpResponse
        resp = HttpResponse(data, content_type='application/json')
        resp.status_code = status
        return resp

    def build_error(self, err):
        data = json.dumps({
            'error': six.text_type(err),
        })
        status = getattr(err, 'status', 500)
        return self.build_response(data, status=status)

    def is_debug(self):
        return False

    def handle(self, endpoint, *args, **kwargs):
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

            deserialize_method = getattr(self, 'deserialize_{0}'.format(endpoint))
            self.data = deserialize_method()

            method = getattr(self, self.http_methods[endpoint][method])
            data = method(*args, **kwargs)

            serialize_method = getattr(self, 'serialize_{0}'.format(endpoint))
            serialized = serialize_method(data)
        except Exception as err:
            if self.is_debug():
                raise

            return self.build_error(err)

        return self.build_response(serialized, status=self.status_map.get(method, OK))

    def deserialize_list(self):
        # By default, Django-esque.
        if self.request.body:
            return json.loads(self.request.body)

        return []

    def deserialize_detail(self):
        # By default, Django-esque.
        if self.request.body:
            return json.loads(self.request.body)

        return {}

    def serialize_list(self, data):
        if data is None:
            return ''

        final_data = [self.prepare(item) for item in data]
        return json.dumps(final_data, cls=MoreTypesJSONEncoder)

    def serialize_detail(self, data):
        if data is None:
            return ''

        final_data = self.prepare(data)
        return json.dumps(final_data, cls=MoreTypesJSONEncoder)

    def prepare(self, data):
        result = {}

        for fieldname, lookup in self.fields.items():
            result[fieldname] = lookup_data(lookup, data)

        return result

    # Common methods the user should implement.

    def list(self, *args, **kwargs):
        raise MethodNotImplemented()

    def detail(self, *args, **kwargs):
        raise MethodNotImplemented()

    def create(self, *args, **kwargs):
        raise MethodNotImplemented()

    def update(self, *args, **kwargs):
        raise MethodNotImplemented()

    def delete(self, *args, **kwargs):
        raise MethodNotImplemented()

    # Uncommon methods the user should implement.
    # These have intentionally uglier method names, which reflects just how
    # much harder they are to get right.

    def update_list(self, *args, **kwargs):
        raise MethodNotImplemented()

    def create_detail(self, *args, **kwargs):
        raise MethodNotImplemented()

    def delete_list(self, *args, **kwargs):
        raise MethodNotImplemented()
