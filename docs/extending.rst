.. _extending:

==================
Extending Restless
==================

Restless is meant to handle many simpler cases well & have enough extensibility
to handle more complex API tasks.

However, a specific goal of the project is to not expand the scope much & simply
give you, the expert on your API, the freedom to build what you need.

We'll be covering:

* Custom endpoints
* Customizing data output
* Adding data validation
* Providing different serialization formats


Custom Endpoints
================

Sometimes you need to provide more than just the typical HTTP verbs. Restless
allows you to hook up custom endpoints that can take advantage of much of the
``Resource``.

Implementing these views requires a couple simple steps:

* Writing the method
* Adding to the ``Resource.http_methods`` mapping
* Adding to your URL routing

For instance, if you wanted to added a schema view (``/api/posts/schema/``)
that responded to ``GET`` requests, you'd first write the method::

    from restless.dj import DjangoResource
    from restless.resources import skip_prepare


    class PostResource(DjangoResource):
        # The usual methods, then...

        @skip_prepare
        def schema(self):
            # Return your schema information.
            # We're keeping it simple (basic field names & data types).
            return {
                'fields': {
                    'id': 'integer',
                    'title': 'string',
                    'author': 'string',
                    'body': 'string',
                },
            }

The next step is to update the :py:attr:`Resource.http_methods`. This can
either be fully written out in your class or (as I prefer) a small extension
to your ``__init__``...::

    from restless.dj import DjangoResource
    from restless.resources import skip_prepare


    class PostResource(DjangoResource):
        # We'll lightly extend the ``__init__``.
        def __init__(self, *args, **kwargs):
            super(PostResource, self).__init__(*args, **kwargs)

            # Add on a new top-level key, then define what HTTP methods it
            # listens on & what methods it calls for them.
            self.http_methods.update({
                'schema': {
                    'GET': 'schema',
                }
            })

        # The usual methods, then...

        @skip_prepare
        def schema(self):
            return {
                'fields': {
                    'id': 'integer',
                    'title': 'string',
                    'author': 'string',
                    'body': 'string',
                },
            }

Finally, it's just a matter of hooking up the URLs as well. You can do this
manually or (once again) by extending a built-in method.::

    # Add the correct import here.
    from django.conf.urls import url

    from restless.dj import DjangoResource
    from restless.resources import skip_prepare


    class PostResource(DjangoResource):
        def __init__(self, *args, **kwargs):
            super(PostResource, self).__init__(*args, **kwargs)
            self.http_methods.update({
                'schema': {
                    'GET': 'schema',
                }
            })

        # The usual methods, then...

        # Note: We're using the ``skip_prepare`` decorator here so that Restless
        # doesn't run ``prepare`` on the schema data.
        # If your custom view returns a typical ``object/dict`` (like the
        # ``detail`` method), you can omit this.
        @skip_prepare
        def schema(self):
            return {
                'fields': {
                    'id': 'integer',
                    'title': 'string',
                    'author': 'string',
                    'body': 'string',
                },
            }

        # Finally, extend the URLs.
        @classmethod
        def urls(cls, name_prefix=None):
            urlpatterns = super(PostResource, cls).urls(name_prefix=name_prefix)
            return [
                url(r'^schema/$', cls.as_view('schema'), name=cls.build_url_name('schema', name_prefix)),
            ] + urlpatterns

.. note::

    This step varies from framework to framework around hooking up the
    URLs/routes. The code is specific to the
    :py:class:`restless.dj.DjangoResource`, but the approach is the same
    regardless.

You should now be able to hit something like http://127.0.0.1/api/posts/schema/
in your browser & get a JSON schema view!


Customizing Data Output
=======================

There are four approaches to customizing your data ouput.

#. The built-in ``Preparer/FieldsPreparer`` (simple)
#. The included ``SubPreparer/CollectionSubPreparer`` (slightly more complex)
#. Overriding :py:meth:`restless.resources.Resource.prepare` (happy medium)
#. Per-method data (flexible but most work)

Fields
------

Using ``FieldsPreparer`` is documented elsewhere (see the :ref:`tutorial`), but
the basic gist is that you create a ``FieldsPreparer`` instance & assign it
on your resource class. It takes a ``fields`` parameter, which should be a
dictionary of fields to expose. Example::

    class MyResource(Resource):
        preparer = FieldsPreparer(fields={
            # Expose the same name.
            "id": "id",
            # Rename a field.
            "author": "username",
            # Access deeper data.
            "type_id": "metadata.type.pk",
        })

This dictionary is a mapping, with keys representing the final name & the
values acting as a lookup path.

If the lookup path **has no** periods (i.e. ``name``) in it, it's
considered to be an attribute/key on the item being processed. If that item
looks like a ``dict``, key access is attempted. If it looks like an ``object``,
attribute access is used. In either case, the found value is returned.

If the lookup path **has** periods (i.e. ``entry.title``), it is split on the
periods (like a Python import path) and recursively uses the previous value to
look up the next value until a final value is found.


Subpreparers & Collections
--------------------------

Sometimes, your data isn't completely flat but is instead nested. This
frequently occurs in conjunction with related data, such as a foreign key'd
object or many-to-many scenario. In this case, you can lever "subpreparers".
Restless ships with two of these, the ``SubPreparer`` & the
``CollectionSubPreparer``.

The ``SubPreparer`` is useful for a single nested relation. You define a
regular ``Preparer/FieldsPreparer`` (perhaps in a shareable location), then
use the ``SubPreparer`` to pull it in & incorporate the nested data. For
example::

    # We commonly expose author information in our API as nested data.
    # This definition can happen in its own module or wherever needed.
    author_preparer = FieldsPreparer(fields={
        'id': 'pk',
        'username': 'username',
        'name': 'get_full_name',
    })

    # ...

    # Then, in the main preparer, pull them in using `SubPreparer`.
    preparer = FieldsPreparer(fields={
        'author': SubPreparer('user', author_preparer),
        # Other fields can come before/follow as normal.
        'content': 'post',
        'created': 'created_at',
    })

This results in output like::

    {
        "content": "Isn't my blog cool? I think so...",
        "created": "2017-05-22T10:34:48",
        "author": {
            "id": 5,
            "username": "joe",
            "name": "Joe Bob"
        }
    }

The ``CollectionSubPreparer`` operates on the same principle (define a set
of fields to be nested), but works with collections of things. These collections
should be ordered & behave similar to iterables like ``list``s & ``tuples``.
As an example::

    # Set up a preparer that handles the data for each thing in the broader
    # collection.
    # Again, this can be in its own module or just wherever it's needed.
    comment_preparer = FieldsPreparer(fields={
        'comment': 'comment_text',
        'created': 'created',
    })

    # Use it with the ``CollectionSubPreparer`` to create a list
    # of prepared sub items.
    preparer = FieldsPreparer(fields={
        # A normal blog post field.
        'post': 'post_text',
        # All the comments on the post.
        'comments': CollectionSubPreparer('comments.all', comment_preparer),
    })

Which would produce output like::

    {
        "post": "Another day, another blog post.",
        "comments": [
            {
                "comment": "I hear you. Boring day here too.",
                "created": "2017-05-23T16:43:22"
            },
            {
                "comment": "SPAM SPAM SPAM",
                "created": "2017-05-24T21:21:21"
            }
        ]
    }


Overriding ``prepare``
----------------------

For every item (``object`` or ``dict``) that gets serialized as output, it runs
through a ``prepare`` method on your ``Resource`` subclass.

The default behavior checks to see if you have ``fields`` defined on your class
& either just returns all the data (if there's no ``fields``) or uses the
``fields`` to extract plain data.

However, you can use/abuse this method for your own nefarious purposes. For
example, if you wanted to serve an API of users but sanitize the data, you
could do something like::

    from django.contrib.auth.models import User

    from restless.dj import DjangoResource
    from restless.preparers import FieldsPreparer


    class UserResource(DjangoResource):
        preparer = FieldsPreparer(fields={
            'id': 'id',
            'username': 'username',
            # We're including email here, but we'll sanitize it later.
            'email': 'email',
            'date_joined': 'date_joined',
        })

        def list(self):
            return User.objects.all()

        def detail(self, pk):
            return User.objects.get(pk=pk)

        def prepare(self, data):
            # ``data`` is the object/dict to be exposed.
            # We'll call ``super`` to prep the data, then we'll mask the email.
            prepped = super(UserResource, self).prepare(data)

            email = prepped['email']
            at_offset = email.index('@')
            prepped['email'] = email[:at_offset + 1] + "..."

            return prepped

This example is somewhat contrived, but you can perform any kind of
transformation you want here, as long as you return a plain, serializable
``dict``.


Per-Method Data
---------------

Because Restless can serve plain old Python objects (anything JSON serializable
+ ``datetime`` + ``decimal``), the ultimate form of control is simply to load
your data however you want, then return a simple/serializable form.

For example, Django's ``models.Model`` classes are not normally
JSON-serializable. We also may want to expose related data in a nested form.
Here's an example of doing something like that.::

    from restless.dj import DjangoResource

    from posts.models import Post


    class PostResource(DjangoResource):
        def detail(self, pk):
            # We do our rich lookup here.
            post = Post.objects.get(pk=pk).select_related('user')

            # Then we can simplify it & include related information.
            return {
                'title': post.title,
                'author': {
                    'id': post.user.id,
                    'username': post.user.username,
                    'date_joined': post.user.date_joined,
                    # We exclude things like ``password`` & ``email`` here
                    # intentionally.
                },
                'body': post.content,
                # ...
            }

While this is more verbose, it gives you all the control.

If you have resources for your nested data, you can also re-use them to make the
construction easier. For example::

    from django.contrib.auth.models import User

    from restless.dj import DjangoResource
    from restless.preparers import FieldsPreparer

    from posts.models import Post


    class UserResource(DjangoResource):
        preparer = FieldsPreparer(fields={
            'id': 'id',
            'username': 'username',
            'date_joined': 'date_joined',
        })

        def detail(self, pk):
            return User.objects.get(pk=pk)


    class PostResource(DjangoResource):
        def detail(self, pk):
            # We do our rich lookup here.
            post = Post.objects.get(pk=pk).select_related('user')

            # Instantiate the ``UserResource``
            ur = UserResource()

            # Then populate the data.
            return {
                'title': post.title,
                # We leverage the ``prepare`` method from above to build the
                # nested data we want.
                'author': ur.prepare(post.user),
                'body': post.content,
                # ...
            }


Data Validation
===============

Validation can be a contentious issue. No one wants to risk data corruption
or security holes in their services. However, there's no real standard or
consensus on doing data validation even within the **individual** framework
communities themselves, let alone *between* frameworks.

So unfortunately, Restless mostly ignores this issue, leaving you to do data
validation the way you think is best.

The good news is that the data you'll need to validate is already in a
convenient-to-work-with dictionary called ``Resource.data`` (assigned
immediately after deserialization takes place).

The recommended approach is to simply add on to your data methods themselves.
For example, since Django ``Form`` objects are at least *bundled* with the
framework, we'll use those as an example...::

    from django.forms import ModelForm

    from restless.dj import DjangoResource
    from restless.exceptions import BadRequest


    class UserForm(ModelForm):
        class Meta(object):
            model = User
            fields = ['username', 'first_name', 'last_name', 'email']


    class UserResource(DjangoResource):
        preparer = FieldsPreparer(fields={
            "id": "id",
            "username": "username",
            "first_name": "first_name",
            "last_name": "last_name",
            "email": "email",
        })

        def create(self):
            # We can create a bound form from the get-go.
            form = UserForm(self.data)

            if not form.is_valid():
                raise BadRequest('Something is wrong.')

            # Continue as normal, using the form data instead.
            user = User.objects.create(
                username=form.cleaned_data['username'],
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                email=form.cleaned_data['email'],
            )
            return user

If you're going to use this validation in other places, you're welcome to DRY
up your code into a validation method. An example of this might look like...::

    from django.forms import ModelForm

    from restless.dj import DjangoResource
    from restless.exceptions import BadRequest


    class UserForm(ModelForm):
        class Meta(object):
            model = User
            fields = ['username', 'first_name', 'last_name', 'email']


    class UserResource(DjangoResource):
        preparer = FieldsPreparer(fields={
            "id": "id",
            "username": "username",
            "first_name": "first_name",
            "last_name": "last_name",
            "email": "email",
        })

        def validate_user(self):
            form = UserForm(self.data)

            if not form.is_valid():
                raise BadRequest('Something is wrong.')

            return form.cleaned_data

        def create(self):
            cleaned = self.validate_user()
            user = User.objects.create(
                username=cleaned['username'],
                first_name=cleaned['first_name'],
                last_name=cleaned['last_name'],
                email=cleaned['email'],
            )
            return user

        def update(self, pk):
            cleaned = self.validate_user()
            user = User.objects.get(pk=pk)
            user.username = cleaned['username']
            user.first_name = cleaned['first_name']
            user.last_name = cleaned['last_name']
            user.email = cleaned['email']
            user.save()
            return user


Alternative Serialization
=========================

For some, Restless' JSON-only syntax might not be appealing. Fortunately,
overriding this is not terribly difficult.

For the purposes of demonstration, we'll implement YAML in place of JSON.
The process would be similar (but much more verbose) for XML (& brings
`a host of problems`_ as well).

Start by creating a ``Serializer`` subclass for the YAML. We'll override
a couple methods there. This code can live anywhere, as long as it is
importable for your ``Resource``.::

    import yaml

    from restless.serializers import Serializer


    class YAMLSerializer(Serializer):
        def deserialize(self, body):
            # Do **NOT** use ``yaml.load`` here, as it can contain things like
            # *functions* & other dangers!
            return yaml.safe_load(body)

        def serialize(self, data):
            return yaml.dump(data)

Once that class has been created, it's just a matter of assigning an instance
onto your ``Resource``.::

    # Old.
    class MyResource(Resource):
        # This was present by default.
        serializer = JSONSerializer()

    # New.
    class MyResource(Resource):
        serializer = YAMLSerializer()

You can even do things like handle multiple serialization formats, say if the
user provides a ``?format=yaml`` GET param...::

    from restless.serializers import Serializer
    from restless.utils import json, MoreTypesJSONEncoder

    from django.template import Context, Template


    class MultiSerializer(Serializer):
        def deserialize(self, body):
            # This is Django-specific, but all frameworks can handle GET
            # parameters...
            ct = request.GET.get('format', 'json')

            if ct == 'yaml':
                return yaml.safe_load(body)
            else:
                return json.load(body)

        def serialize(self, data):
            # Again, Django-specific.
            ct = request.GET.get('format', 'json')

            if ct == 'yaml':
                return yaml.dump(body)
            else:
                return json.dumps(body, cls=MoreTypesJSONEncoder)

.. _`a host of problems`: https://pypi.python.org/pypi/defusedxml

