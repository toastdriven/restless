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
    def add_views(cls, config, rule_prefix, routename_prefix=None):
        """
        A convenience method for registering the routes and views in pyramid.

        This automatically adds a list and detail endpoint to your routes.

        :param config: The pyramid ``Configurator`` object for your app.
        :type config: ``pyramid.config.Configurator``

        :param rule_prefix: The start of the URL to handle.
        :type rule_prefix: string

        :param routename_prefix: (Optional) A prefix for the route's name.
            The default is ``None``, which will autocreate a prefix based on the
            class name. Ex: ``PostResource`` -> ``api_post_list``
        :type routename_prefix: string

        :returns: ``pyramid.config.Configurator``
        """
        methods = ('GET', 'POST', 'PUT', 'DELETE')
        if routename_prefix is None:
            routename_prefix = 'api_{0}'.format(
                cls.__name__.replace('Resource', '').lower()
            )
        config.add_route(
            routename_prefix + '_list',
            rule_prefix
        )
        config.add_view(
            cls.as_list(),
            route_name=routename_prefix + '_list',
            request_method=methods
        )

        config.add_route(
            routename_prefix + '_detail',
            rule_prefix + '{name}/'
        )
        config.add_view(
            cls.as_detail(),
            route_name=routename_prefix + '_detail',
            request_method=methods
        )
        return config

