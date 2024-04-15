import unittest

from restless.preparers import (CollectionSubPreparer, SubPreparer,
                                FieldsPreparer)


class InstaObj:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def dont(self):
        return {'panic': 'vogon'}


class LookupDataTestCase(unittest.TestCase):
    def setUp(self):
        super(LookupDataTestCase, self).setUp()
        self.preparer = FieldsPreparer(fields=None)
        self.obj_data = InstaObj(
            say='what',
            count=453,
            moof={
                'buried': {
                    'id': 7,
                    'data': InstaObj(yes='no')
                }
            },
            parent=None
        )
        self.dict_data = {
            'hello': 'world',
            'abc': 123,
            'more': {
                'things': 'here',
                'nested': InstaObj(
                    awesome=True,
                    depth=3
                ),
            },
            'parent': None,
            'who': [
                {'name': 'Ford'},
                {'name': 'Arthur'},
                {'name': 'Beeblebrox'},
            ],
            'dont': lambda: {
                'panic': 'vogon',
            },
        }

    def test_dict_simple(self):
        self.assertEqual(self.preparer.lookup_data('hello', self.dict_data), 'world')
        self.assertEqual(self.preparer.lookup_data('abc', self.dict_data), 123)

    def test_obj_simple(self):
        self.assertEqual(self.preparer.lookup_data('say', self.obj_data), 'what')
        self.assertEqual(self.preparer.lookup_data('count', self.obj_data), 453)

    def test_dict_nested(self):
        self.assertEqual(self.preparer.lookup_data('more.things', self.dict_data), 'here')
        self.assertEqual(self.preparer.lookup_data('more.nested.depth', self.dict_data), 3)

    def test_obj_nested(self):
        self.assertEqual(self.preparer.lookup_data('moof.buried.id', self.obj_data), 7)
        self.assertEqual(self.preparer.lookup_data('moof.buried.data.yes', self.obj_data), 'no')

    def test_dict_miss(self):
        with self.assertRaises(KeyError):
            self.preparer.lookup_data('another', self.dict_data)

    def test_obj_miss(self):
        with self.assertRaises(AttributeError):
            self.preparer.lookup_data('whee', self.obj_data)

    def test_dict_nullable_fk(self):
        self.assertIsNone(self.preparer.lookup_data('parent.id', self.dict_data))

    def test_obj_nullable_fk(self):
        self.assertIsNone(self.preparer.lookup_data('parent.id', self.obj_data))

    def test_empty_lookup(self):
        # We could possibly get here in the recursion.
        self.assertEqual(self.preparer.lookup_data('', 'Last value'), 'Last value')

    def test_complex_miss(self):
        with self.assertRaises(AttributeError):
            self.preparer.lookup_data('more.nested.nope', self.dict_data)

    def test_obj_callable(self):
        self.assertEqual(
            self.preparer.lookup_data('dont.panic', self.obj_data),
            'vogon',
        )

    def test_dict_callable(self):
        self.assertEqual(
            self.preparer.lookup_data('dont.panic', self.dict_data),
            'vogon',
        )

    def test_prepare_simple(self):
        preparer = FieldsPreparer(fields={
            'flying': 'say',
        })
        preped = preparer.prepare(self.obj_data)
        self.assertEqual(preped, {'flying': 'what'})

    def test_prepare_subpreparer(self):
        subpreparer = FieldsPreparer(fields={
            'id': 'id',
            'data': 'data',
        })
        preparer = FieldsPreparer(fields={
            'flying': 'say',
            'wale': SubPreparer('moof.buried', subpreparer),
        })
        preped = preparer.prepare(self.obj_data)

    def test_prepare_subsubpreparer(self):
        subsubpreparer = FieldsPreparer(fields={
            'really': 'yes',
        })
        subpreparer = FieldsPreparer(fields={
            'data': SubPreparer('data', subsubpreparer),
        })
        preparer = FieldsPreparer(fields={
            'wale': SubPreparer('moof.buried', subpreparer),
        })
        preped = preparer.prepare(self.obj_data)
        self.assertEqual(preped, {'wale': {'data': {'really': 'no'}}})

    def test_prepare_collection_subpreparer(self):
        subpreparer = FieldsPreparer(fields={
            'name': 'name',
        })
        preparer = FieldsPreparer(fields={
            'who': CollectionSubPreparer('who', subpreparer),
        })
        preped = preparer.prepare(self.dict_data)
        self.assertEqual(preped, {'who': [
            {'name': 'Ford'},
            {'name': 'Arthur'},
            {'name': 'Beeblebrox'},
        ]})
