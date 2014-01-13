from django.conf import settings
from django.conf.urls import patterns, url
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from .resources import Resource


class DjangoResource(Resource):
    """
    A Django-specific ``Resource`` subclass.

    Doesn't require any special configuration, but helps when working in a
    Django environment.
    """
    # Because Django.
    @classmethod
    def as_list(self, *args, **kwargs):
        return csrf_exempt(super(DjangoResource, self).as_list(*args, **kwargs))

    @classmethod
    def as_detail(self, *args, **kwargs):
        return csrf_exempt(super(DjangoResource, self).as_detail(*args, **kwargs))

    def is_debug(self):
        # By default, Django-esque.
        return settings.DEBUG

    def build_response(self, data, status=200):
        # By default, Django-esque.
        resp = HttpResponse(data, content_type='application/json')
        resp.status_code = status
        return resp

    @classmethod
    def urls(cls, name_prefix=None):
        """
        A convenience method for hooking up the URLs.

        This automatically adds a list & a detail endpoint to your URLconf.

        :param name_prefix: (Optional) A prefix for the URL's name (for
            resolving). The default is ``None``, which will autocreate a prefix
            based on the class name. Ex: ``BlogPostResource`` ->
            ``api_blog_post_list``
        :type name_prefix: string

        :returns: A ``patterns`` object for ``include(...)``
        """
        if name_prefix is None:
            name_prefix = 'api_{0}'.format(
                cls.__name__.replace('Resource', '').lower()
            )

        return patterns('',
            url(r'^$', cls.as_list(), name=name_prefix + '_list'),
            url(r'^(?P<pk>\d+)/$', cls.as_detail(), name=name_prefix + '_detail'),
        )
