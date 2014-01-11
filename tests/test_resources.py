import unittest

from restless.resources import Resource


class FakeHttpRequest(object):
    def __init__(self, method='GET', body=''):
        self.method = method.upper()
        self.body = body


class FakeHttpResponse(object):
    def __init__(self, body, content_type='text/html'):
        self.body = body
        self.content_type = content_type
        self.status_code = 200


class NonDjangoResource(Resource):
    # Because the default implementation is a tiny-bit Django-specific,
    # we're faking some things here.
    _is_debug = False

    def build_response(self, data, status=200):
        resp = FakeHttpResponse(data, content_type='application/json')
        resp.status_code = status
        return resp

    def is_debug(self):
        return self._is_debug


class ResourceTestCase(unittest.TestCase):
    resource_class = NonDjangoResource

    def setUp(self):
        super(ResourceTestCase, self).setUp()
        self.resource = self.resource_class()

    def test_init(self):
        pass