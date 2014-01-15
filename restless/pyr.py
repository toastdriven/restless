from pyramid.response import Response

from .resources import Resource

class PyramidResource(Resource):
    """
    A Pyramid-specific ``Resource`` subclass.

    Doesn't require any special configuration, but helps when working in a
    Pyramid environment.
    """

    @classmethod
    def as_list(cls, *args, **kwargs):
        return super(PyramidResource, cls).as_list(*args, **kwargs)

    @classmethod
    def as_detail(cls, *init_args, **init_kwargs):
        def _wrapper(request):
            # Make a new instance so that no state potentially leaks between
            # instances.
            inst = cls(*init_args, **init_kwargs)
            inst.request = request
            name = request.matchdict['name']
            return inst.handle('detail', name)

        return _wrapper

    def build_response(self, data, status=200):
        resp = Response(data, status_code=status, content_type="application/json")
        return resp

    @classmethod
    def add_views(cls, config, rule_prefix, endpoint_prefix=None):
        methods = ('GET', 'POST', 'PUT', 'DELETE')
        if endpoint_prefix is None:
            endpoint_prefix = 'api_{0}'.format(
                cls.__name__.replace('Resource', '').lower()
            )
        config.add_route(
            endpoint_prefix + '_list',
            rule_prefix
        )
        config.add_view(
            cls.as_list(),
            route_name=endpoint_prefix + '_list',
            request_method=methods
        )

        config.add_route(
            endpoint_prefix + '_detail',
            rule_prefix + '{name}/'
        )
        config.add_view(
            cls.as_detail(),
            route_name=endpoint_prefix + '_detail',
            request_method=methods
        )
        return config

