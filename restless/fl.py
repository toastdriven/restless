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
    def as_view(cls, view_type, *init_args, **init_kwargs):
        def _wrapper(*args, **kwargs):
            # Overridden here, because Flask uses a global ``request`` object
            # rather than passing it to each view.
            inst = cls(*init_args, **init_kwargs)
            inst.request = request
            return inst.handle(view_type, *args, **kwargs)

        return _wrapper

    def request_body(self):
        return self.request.data

    def is_debug(self):
        from flask import current_app
        return current_app.debug

    def build_response(self, data, status=200):
        return make_response(data, status, {
            'Content-Type': 'application/json'
        })

    @classmethod
    def build_endpoint_name(cls, name, endpoint_prefix=None):
        """
        Given a ``name`` & an optional ``endpoint_prefix``, this generates a name
        for a URL.

        :param name: The name for the URL (ex. 'detail')
        :type name: string

        :param endpoint_prefix: (Optional) A prefix for the URL's name (for
            resolving). The default is ``None``, which will autocreate a prefix
            based on the class name. Ex: ``BlogPostResource`` ->
            ``api_blogpost_list``
        :type endpoint_prefix: string

        :returns: The final name
        :rtype: string
        """
        if endpoint_prefix is None:
            endpoint_prefix = 'api_{0}'.format(
                cls.__name__.replace('Resource', '').lower()
            )

        endpoint_prefix = endpoint_prefix.rstrip('_')
        return '_'.join([endpoint_prefix, name])

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

        app.add_url_rule(
            rule_prefix,
            endpoint=cls.build_endpoint_name('list', endpoint_prefix),
            view_func=cls.as_list(),
            methods=methods
        )
        app.add_url_rule(
            rule_prefix + '<pk>/',
            endpoint=cls.build_endpoint_name('detail', endpoint_prefix),
            view_func=cls.as_detail(),
            methods=methods
        )
