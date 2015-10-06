import unittest

import bottle

from webtest import TestApp

from restless.btl import BottleResource
from restless.utils import json
from restless.exceptions import NotFound
from restless.preparers import FieldsPreparer
from restless.resources import skip_prepare

from .fakes import FakeHttpRequest, FakeModel


class BtlTestResource(BottleResource):

    preparer = FieldsPreparer(fields={
        'id': 'id',
        'title': 'title',
        'author': 'username',
        'body': 'content'
    })
    fake_db = []

    def fake_init(self):
        # Just for testing.
        self.__class__.fake_db = [
            FakeModel(
                id=2,
                title='First post',
                username='viniciuscainelli',
                content='Hello world!'),
            FakeModel(
                id=4,
                title='Another',
                username='viniciuscainelli',
                content='Stuff here.'),
            FakeModel(
                id=5,
                title='Last',
                username='viniciuscainelli',
                content="G'bye!"),
        ]

    def is_authenticated(self):
        if self.request_method() == 'DELETE':
            return False

        return True

    def list(self):
        return self.fake_db

    def detail(self, pk):
        for item in self.fake_db:
            if item.id == pk:
                return item

        raise NotFound('not found :(')

    def create(self):
        self.fake_db.append(FakeModel(
            **self.data
        ))

    def update(self, pk):
        for i in range(len(self.fake_db)):
            if self.fake_db[i].id == pk:
                for k, v in self.data.items():
                    setattr(self.fake_db[i], k, v)
                return


class BottleResourceTestCase(unittest.TestCase):
    def setUp(self):
        super(BottleResourceTestCase, self).setUp()
        self.app = bottle.Bottle()

        self.res = BtlTestResource()
        self.res.prepare_routes(self.app, '/mydata/')

        self.client = TestApp(self.app)

        # Just for the fake data.
        self.res.fake_init()

    def test_list(self):
        res = self.client.get('/mydata/')

        self.assertEqual(res.content_type, 'application/json')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(json.loads(res.body.decode('utf-8')), {
            'objects': [
                {
                    'author': 'viniciuscainelli',
                    'body': 'Hello world!',
                    'id': 2,
                    'title': 'First post'
                },
                {
                    'author': 'viniciuscainelli',
                    'body': 'Stuff here.',
                    'id': 4,
                    'title': 'Another'
                },
                {
                    'author': 'viniciuscainelli',
                    'body': "G'bye!",
                    'id': 5,
                    'title': 'Last'
                }
            ]
        })

    def test_detail(self):
        res = self.client.get('/mydata/4/')

        self.assertEqual(res.content_type, 'application/json')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(json.loads(res.body.decode('utf-8')), {
            'author': 'viniciuscainelli',
            'body': 'Stuff here.',
            'id': 4,
            'title': 'Another'
        })

    def test_create(self):
        res = self.client.post_json('/mydata/', {
            'author': 'viniciuscainelli',
            'body': 'Crazy thing',
            'id': 9,
            'title': 'Hey'
        })

        self.assertEqual(res.content_type, 'application/json')
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.content_length, 0)

    def test_update(self):
        new_data = {
            'author': 'viniciuscainelli',
            'body': 'Stuff here. - edited',
            'id': 4,
            'title': 'Another - edited'
        }
        res = self.client.put_json('/mydata/4/', new_data)

        self.assertEqual(res.content_type, 'application/json')
        self.assertEqual(res.status_code, 202)
        self.assertEqual(res.content_length, 0)
