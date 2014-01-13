from flask import make_response
from flask import request

from .resources import Resource


class FlaskResource(Resource):
    """
    A Flask-specific ``Resource`` subclass.

    Doesn't require any special configuration, but helps when working in a
    Flask environment.
    """
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

    @classmethod
    def add_url_rules(cls, app, rule_prefix, endpoint_prefix=None):
        """
        A convenience method for hooking up the URLs.

        This automatically adds a list & a detail endpoint to your routes.

        :param app: The ``Flask`` object for your app.
        :type app: ``flask.Flask``

        :param rule_prefix: The start of the URL to handle.
        :type rule_prefix: string

        :param endpoint_prefix: (Optional) A prefix for the URL's name (for
            endpoints). The default is ``None``, which will autocreate a prefix
            based on the class name. Ex: ``BlogPostResource`` ->
            ``api_blog_post_list``
        :type endpoint_prefix: string

        :returns: Nothing
        """
        methods = ['GET', 'POST', 'PUT', 'DELETE']

        if endpoint_prefix is None:
            endpoint_prefix = 'api_{0}'.format(
                cls.__name__.replace('Resource', '').lower()
            )

        app.add_url_rule(
            rule_prefix,
            endpoint=endpoint_prefix + '_list',
            view_func=cls.as_list(),
            methods=methods
        )
        app.add_url_rule(
            rule_prefix + '<username>/',
            endpoint=endpoint_prefix + '_detail',
            view_func=cls.as_detail(),
            methods=methods
        )
