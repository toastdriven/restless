from flask import make_response
from flask import request

from .resources import Resource


class FlaskResource(Resource):
    @classmethod
    def as_list(cls, *init_args, **init_kwargs):
        # Overridden here, because Flask uses a global ``request`` object
        # rather than passing it to each view.
        def _wrapper(*args, **kwargs):
            # Make a new instance so that no state potentially leaks between
            # instances.
            inst = cls(*init_args, **init_kwargs)
            inst.request = request
            return inst.handle('list', *args, **kwargs)

        return _wrapper

    @classmethod
    def as_detail(cls, *init_args, **init_kwargs):
        # Overridden here, because Flask uses a global ``request`` object
        # rather than passing it to each view.
        def _wrapper(*args, **kwargs):
            # Make a new instance so that no state potentially leaks between
            # instances.
            inst = cls(*init_args, **init_kwargs)
            inst.request = request
            return inst.handle('detail', *args, **kwargs)

        return _wrapper

    def request_body(self):
        return self.request.data

    def is_debug(self):
        from flask import g
        return g.get('debug')

    def build_response(self, data, status=200):
        return make_response(data, status, {
            'Content-Type': 'application/json'
        })
