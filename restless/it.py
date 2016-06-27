import re

import itty

from restless.constants import OK, NO_CONTENT
from restless.resources import Resource


class IttyResource(Resource):
    """
    A Itty-specific ``Resource`` subclass.

    Doesn't require any special configuration, but helps when working in a
    Itty environment.
    """
    debug = False

    def is_debug(self):
        return self.debug

    def build_response(self, data, status=OK):
        if status == NO_CONTENT:
            # Avoid crashing the client when it tries to parse nonexisting JSON.
            content_type = 'text/plain'
        else:
            content_type = 'application/json'
        return itty.Response(data, status=status, content_type=content_type)

    @classmethod
    def setup_urls(cls, rule_prefix):
        """
        A convenience method for hooking up the URLs.

        This automatically adds a list & a detail endpoint to your request
        mappings.

        :returns: ``None``
        """
        list_url = "%s" % itty.add_slash(rule_prefix)
        detail_url = "%s" % itty.add_slash(rule_prefix + "/(?P<pk>[\w-]+)")

        list_re = re.compile("^%s$" % list_url)
        detail_re = re.compile("^%s$" % detail_url)

        for method in ('GET', 'POST', 'PUT', 'DELETE'):
            itty.REQUEST_MAPPINGS[method].append((list_re, list_url, cls.as_list()))
            itty.REQUEST_MAPPINGS[method].append((detail_re, detail_url, cls.as_detail()))
