import unittest
import socket
import six

from restless.utils import json
from restless.constants import UNAUTHORIZED


def _newer_or_equal_(v):
    for i in six.moves.xrange(min(len(v), len(version_info))):
        expected, tnd = v[i], version_info[i]
        if tnd > expected:
            return True
        elif tnd == expected:
            continue
        else:
            return False
    return True


def _equal_(v):
    return all(
        v[i] == version_info[i]
        for i in six.moves.xrange(min(len(v), len(version_info)))
    )

try:
    from restless.tnd import TornadoResource, _BridgeMixin
    from tornado import testing, web, httpserver, gen, version_info
    from tornado.iostream import IOStream
    if _newer_or_equal_((4, 0, 0, 0)):
        from tornado.http1connection import HTTP1Connection
except ImportError:
    class testing:
        AsyncHTTPTestCase = object

    class web:
        @staticmethod
        def Application(*args, **kw): return False

    class gen:
        @staticmethod
        def coroutine(fn): return fn

    class TornadoResource:
        @staticmethod
        def as_list(): pass

        @staticmethod
        def as_detail(): pass


class TndBaseTestResource(TornadoResource):
    """
    base test resource, containing a fake-db
    """
    fake_db = []

    def __init__(self):
        # Just for testing.
        self.__class__.fake_db = [
            {"id": "dead-beef", "title": 'First post'},
            {"id": "de-faced", "title": 'Another'},
            {"id": "bad-f00d", "title": 'Last'},
        ]


class TndBasicTestResource(TndBaseTestResource):
    """
    containing several basic view_method
    """
    def list(self):
        return self.fake_db

    def detail(self, pk):
        return next((item for item in self.fake_db if item['id'] == pk), None)

    def create(self):
        self.fake_db.append(self.data)


class TndAsyncTestResource(TndBaseTestResource):
    """
    asynchronous basic view_method
    """
    @gen.coroutine
    def list(self):
        raise gen.Return(self.fake_db)

    @gen.coroutine
    def detail(self, pk):
        for item in self.fake_db:
            if item['id'] == pk:
                raise gen.Return(item)
        raise gen.Return(None)

    @gen.coroutine
    def create(self):
        self.fake_db.append(self.data)


app = web.Application([
    (r'/fake', TndBasicTestResource.as_list()),
    (r'/fake/([^/]+)', TndBasicTestResource.as_detail()),
    (r'/fake_async', TndAsyncTestResource.as_list()),
    (r'/fake_async/([^/]+)', TndAsyncTestResource.as_detail())
], debug=True)


@unittest.skipIf(not app, 'Tornado is not available')
class BaseHTTPTestCase(testing.AsyncHTTPTestCase):
    """
    base of test case
    """
    def get_app(self):
        return app


@unittest.skipIf(not app, 'Tornado is not available')
class TndResourceTestCase(BaseHTTPTestCase):
    """
    """
    def test_as_list(self):
        resp = self.fetch(
            '/fake',
            method='GET',
            follow_redirects=False
        )
        self.assertEqual(resp.headers['Content-Type'], 'application/json; charset=UTF-8')
        self.assertEqual(resp.code, 200)
        self.assertEqual(json.loads(resp.body.decode('utf-8')), {
            'objects': [
                {
                    'id': 'dead-beef',
                    'title': 'First post'
                },
                {
                    'id': 'de-faced',
                    'title': 'Another'
                },
                {
                    'id': 'bad-f00d',
                    'title': 'Last'
                }
            ]
        })

    def test_as_detail(self):
        resp = self.fetch(
            '/fake/de-faced',
            method='GET',
            follow_redirects=False
        )
        self.assertEqual(resp.headers['Content-Type'], 'application/json; charset=UTF-8')
        self.assertEqual(resp.code, 200)
        self.assertEqual(json.loads(resp.body.decode('utf-8')), {
            'id': 'de-faced',
            'title': 'Another'
        })

    def test_not_authenticated(self):
        resp = self.fetch(
                '/fake',
                method='POST',
                body='{"id": 7, "title": "Moved hosts"}',
                follow_redirects=False
        )
        self.assertEqual(resp.code, UNAUTHORIZED)


@unittest.skipIf(not app, 'Tornado is not available')
class BaseTestCase(unittest.TestCase):
    """
    test case that export the wrapped tornado.web.RequestHandler.
    """
    def init_request_handler(self, rh_cls, view_type):
        global app
        if view_type == 'list':
            rq = rh_cls.as_list()
        elif view_type == 'detail':
            rq = rh_cls.as_detail()

        # compose a fake incoming request
        fake_connection = None

        # after tornado 4.1, it's not allowed to build a RequestHandler without a connection.
        if _newer_or_equal_((4, 0, 0, 0)):
            ios = IOStream(socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0))
            context = None

            # there is a bug in these 2 version that would fail when
            # context is None
            if _equal_((4, 0, 1)) or _equal_((4, 0, 2)):
                context = httpserver._HTTPRequestContext(ios, None, None)
            fake_connection = HTTP1Connection(ios, False, context=context)
        fake_request = httpserver.HTTPRequest('GET', '/fake', body='test123', connection=fake_connection)
        self.new_handler = rq(app, fake_request)


@unittest.skipIf(not app, 'Tornado is not available')
class InternalTestCase(BaseTestCase):
    """
    test-cases that check internal structure of the wrapped
    tornado.web.RequestHandler
    """
    def setUp(self):
        self.init_request_handler(TndBasicTestResource, 'list')

    def test_is_debug(self):
        ori_debug = app.settings['debug']

        app.settings['debug'] = False
        self.assertFalse(self.new_handler.resource_handler.is_debug())

        app.settings['debug'] = True
        self.assertTrue(self.new_handler.resource_handler.is_debug())

        app.settings['debug'] = ori_debug

    def test_body(self):
        self.assertEqual(self.new_handler.resource_handler.request_body(), 'test123')

    def test_method(self):
        self.assertEqual(self.new_handler.resource_handler.request_method(), 'GET')

    def test_class(self):
        """ test the generated tornado.web.RequestHandler """
        self.assertEqual(self.new_handler.__class__.__name__, 'TndBasicTestResource__BridgeMixin_restless')
        self.assertIn(_BridgeMixin, self.new_handler.__class__.__mro__)
        self.assertIn(web.RequestHandler, self.new_handler.__class__.__mro__)

    def test_var(self):
        """ make sure variable from tornado is correctly passed. """
        self.assertTrue(hasattr(self.new_handler.resource_handler, 'request'))
        self.assertTrue(hasattr(self.new_handler.resource_handler, 'application'))


@unittest.skipIf(not app, 'Tornado is not available')
class TndDeleteTestResource(TndBasicTestResource):
    """
    testing inherited resource
    """
    def delete(self, pk):
        self.fake_db = filter(lambda x: x['id'] != pk, self.fake_db)

    def delete_list(self):
        self.fake_db = {}


@unittest.skipIf(not app, 'Tornado is not available')
class FuncTrimTestCase(BaseTestCase):
    """
    test-cases that make sure we removed unnecessary handler functions
    of the wrapped tornado.web.RequestHandler
    """
    def test_empty_resource(self):
        self.init_request_handler(TndBaseTestResource, 'list')
        self.assertNotIn('post', self.new_handler.__class__.__dict__)
        self.assertNotIn('get', self.new_handler.__class__.__dict__)
        self.assertNotIn('delete', self.new_handler.__class__.__dict__)
        self.assertNotIn('put', self.new_handler.__class__.__dict__)

    def test_basic_resource_list(self):
        self.init_request_handler(TndBasicTestResource, 'list')
        self.assertIn('post', self.new_handler.__class__.__dict__)
        self.assertIn('get', self.new_handler.__class__.__dict__)
        self.assertNotIn('delete', self.new_handler.__class__.__dict__)
        self.assertNotIn('put', self.new_handler.__class__.__dict__)

    def test_basic_resource_detail(self):
        self.init_request_handler(TndBasicTestResource, 'detail')
        self.assertNotIn('post', self.new_handler.__class__.__dict__)
        self.assertIn('get', self.new_handler.__class__.__dict__)
        self.assertNotIn('delete', self.new_handler.__class__.__dict__)
        self.assertNotIn('put', self.new_handler.__class__.__dict__)

    def test_inheritance_resource_detail(self):
        self.init_request_handler(TndDeleteTestResource, 'detail')
        self.assertNotIn('post', self.new_handler.__class__.__dict__)
        self.assertIn('get', self.new_handler.__class__.__dict__)
        self.assertIn('delete', self.new_handler.__class__.__dict__)
        self.assertNotIn('put', self.new_handler.__class__.__dict__)


@unittest.skipIf(not app, 'Tornado is not available')
class TndAsyncResourceTestCase(BaseHTTPTestCase):
    """
    test asynchronous view_method
    """
    def test_as_list(self):
        resp = self.fetch(
            '/fake_async',
            method='GET',
            follow_redirects=False
        )
        self.assertEqual(resp.headers['Content-Type'], 'application/json; charset=UTF-8')
        self.assertEqual(resp.code, 200)
        self.assertEqual(json.loads(resp.body.decode('utf-8')), {
            'objects': [
                {
                    'id': 'dead-beef',
                    'title': 'First post'
                },
                {
                    'id': 'de-faced',
                    'title': 'Another'
                },
                {
                    'id': 'bad-f00d',
                    'title': 'Last'
                }
            ]
        })

    def test_as_detail(self):
        resp = self.fetch(
            '/fake_async/de-faced',
            method='GET',
            follow_redirects=False
        )
        self.assertEqual(resp.headers['Content-Type'], 'application/json; charset=UTF-8')
        self.assertEqual(resp.code, 200)
        self.assertEqual(json.loads(resp.body.decode('utf-8')), {
            'id': 'de-faced',
            'title': 'Another'
        })

