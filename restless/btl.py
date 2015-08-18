from bottle import request, response

from .resources import Resource


class BottleResource(Resource):
    """
    A Bottle-specific ``Resource`` subclass.

    Doesn't require any special configuration, but helps when working in a
    Bottle environment.
    """
    @classmethod
    def as_list(cls, *init_args, **init_kwargs):
        # Using the global ``request`` object.
        def _wrapper(*args, **kwargs):
            # Make a new instance so that no state potentially leaks between
            # instances.
            inst = cls(*init_args, **init_kwargs)
            inst.request = request
            return inst.handle('list', *args, **kwargs)

        return _wrapper

    @classmethod
    def as_detail(cls, *init_args, **init_kwargs):
        # Using the global ``request`` object.
        def _wrapper(*args, **kwargs):
            # Make a new instance so that no state potentially leaks between
            # instances.
            inst = cls(*init_args, **init_kwargs)
            inst.request = request
            return inst.handle('detail', *args, **kwargs)

        return _wrapper

    def request_body(self):
        return self.request.body.read()

    def is_debug(self):
        from bottle import DEBUG
        return DEBUG

    def build_response(self, data, status=200):
        response.status = status
        response.content_type = 'application/json'
        return data

    @classmethod
    def build_url_name(cls, name, name_prefix=None):
        """
        Given a ``name`` & an optional ``name_prefix``, this generates a name
        for a URL.
        :param name: The name for the URL (ex. 'detail')
        :type name: string
        :param name_prefix: (Optional) A prefix for the URL's name (for
            resolving). The default is ``None``, which will autocreate a prefix
            based on the class name. Ex: ``BlogPostResource`` ->
            ``api_blog_post_list``
        :type name_prefix: string
        :returns: The final name
        :rtype: string
        """
        if name_prefix is None:
            name_prefix = 'api_{0}'.format(
                cls.__name__.replace('Resource', '').lower()
            )

        name_prefix = name_prefix.rstrip('_')
        return '_'.join([name_prefix, name])

    @classmethod
    def prepare_routes(cls, app, url_prefix='/', name_prefix=None):
        """
        A convenience method for hooking up the URLs.
        This automatically adds a list & a detail endpoint to your routes.
        :param app: The ``Bottle`` object for your app.
        :type app: ``bottle.Bottle``
        :param url_prefix: The start of the URL to handle.
        :type url_prefix: string
        :param name_prefix: (Optional) A prefix for the URL's name.
            The default is ``None``, which will autocreate a prefix
            based on the class name. Ex: ``BlogPostResource`` ->
            ``api_blog_post_list``
        :type name_prefix: string
        :returns: Nothing
        """
        methods = ['GET', 'POST', 'PUT', 'DELETE']

        app.route(
            path=url_prefix,
            name=cls.build_url_name('list', name_prefix),
            callback=cls.as_list(),
            method=methods
        )
        app.route(
            path=url_prefix + '<pk:int>/',
            name=cls.build_url_name('detail', name_prefix),
            callback=cls.as_detail(),
            method=methods
        )
