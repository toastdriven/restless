import six

from django.conf import settings
from django.conf.urls import url
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator
from django.http import HttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt

from .constants import OK, NO_CONTENT
from .exceptions import NotFound, BadRequest
from .resources import Resource


class DjangoResource(Resource):
    """
    A Django-specific ``Resource`` subclass.

    Doesn't require any special configuration, but helps when working in a
    Django environment.
    """

    def serialize_list(self, data):
        if data is None:
            return super(DjangoResource, self).serialize_list(data)

        if getattr(self, 'paginate', False):
            page_size = getattr(self, 'page_size', getattr(settings, 'RESTLESS_PAGE_SIZE', 10))
            paginator = Paginator(data, page_size)

            page_number = self.request.GET.get('p', 1)

            if page_number not in paginator.page_range:
                raise BadRequest('Invalid page number')

            self.page = paginator.page(page_number)
            data = self.page.object_list

        return super(DjangoResource, self).serialize_list(data)

    def wrap_list_response(self, data):
        response_dict = super(DjangoResource, self).wrap_list_response(data)

        if hasattr(self, 'page'):
            next_page = self.page.has_next() and self.page.next_page_number() or None
            previous_page = self.page.has_previous() and self.page.previous_page_number() or None

            response_dict['pagination'] = {
                'num_pages': self.page.paginator.num_pages,
                'count': self.page.paginator.count,
                'page': self.page.number,
                'start_index': self.page.start_index(),
                'end_index': self.page.end_index(),
                'next_page': next_page,
                'previous_page': previous_page,
                'per_page': self.page.paginator.per_page,
            }

        return response_dict

    # Because Django.
    @classmethod
    def as_list(self, *args, **kwargs):
        return csrf_exempt(super(DjangoResource, self).as_list(*args, **kwargs))

    @classmethod
    def as_detail(self, *args, **kwargs):
        return csrf_exempt(super(DjangoResource, self).as_detail(*args, **kwargs))

    def is_debug(self):
        return settings.DEBUG

    def build_response(self, data, status=OK):
        if status == NO_CONTENT:
            # Avoid crashing the client when it tries to parse nonexisting JSON.
            content_type = 'text/plain'
        else:
            content_type = 'application/json'
        resp = HttpResponse(data, content_type=content_type, status=status)
        return resp

    def build_error(self, err):
        # A bit nicer behavior surrounding things that don't exist.
        if isinstance(err, (ObjectDoesNotExist, Http404)):
            err = NotFound(msg=six.text_type(err))

        return super(DjangoResource, self).build_error(err)

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
            name_prefix = 'api_{}'.format(
                cls.__name__.replace('Resource', '').lower()
            )

        name_prefix = name_prefix.rstrip('_')
        return '_'.join([name_prefix, name])

    @classmethod
    def urls(cls, name_prefix=None):
        """
        A convenience method for hooking up the URLs.

        This automatically adds a list & a detail endpoint to your URLconf.

        :param name_prefix: (Optional) A prefix for the URL's name (for
            resolving). The default is ``None``, which will autocreate a prefix
            based on the class name. Ex: ``BlogPostResource`` ->
            ``api_blogpost_list``
        :type name_prefix: string

        :returns: A list of ``url`` objects for ``include(...)``
        """
        return [
            url(r'^$', cls.as_list(), name=cls.build_url_name('list', name_prefix)),
            url(r'^(?P<pk>[\w-]+)/$', cls.as_detail(), name=cls.build_url_name('detail', name_prefix)),
        ]
