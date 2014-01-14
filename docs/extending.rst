.. _extending:

==================
Extending Restless
==================

Restless is meant to handle many simpler cases well & have enough extensibility
to handle more complex API tasks.

However, a specific goal of the project is to not expand the scope much & simply
give you, the expert on your API, the freedom to build what you need.

We'll be covering:

* Customizing data output
* Adding data validation
* Providing different serialization formats


Customizing Data Output
=======================

There are three approaches to customizing your data ouput.

#. The built-in ``fields`` (simple)
#. Overriding :py:meth:`restless.resources.Resource.prepare` (happy medium)
#. Per-method data (flexible but most work)

Fields
------

Using ``fields`` is documented elsewhere (see the :ref:`tutorial`), but the
basic gist is that you define a dictionary on the **class**. Example::

    class MyResource(Resource):
        fields = {
            # Expose the same name.
            "id": "id",
            # Rename a field.
            "author": "username",
            # Access deeper data.
            "type_id": "metadata.type.pk",
        }

This dictionary is a mapping, with keys representing the final name & the
values acting as a lookup path.

If the lookup path **has no** periods (i.e. ``name``) in it, it's
considered to be an attribute/key on the item being processed. If that item
looks like a ``dict``, key access is attempted. If it looks like an ``object``,
attribute access is used. In either case, the found value is returned.

If the lookup path **has** periods (i.e. ``entry.title``), it is split on the
periods (like a Python import path) and recursively uses the previous value to
look up the next value until a final value is found.


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


    class UserResource(DjangoResource):
        fields = {
            'id': 'id',
            'username': 'username',
            # We're including email here, but we'll sanitize it later.
            'email': 'email',
            'date_joined': 'date_joined',
        }

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

    from posts.models import Post


    class UserResource(DjangoResource):
        fields = {
            'id': 'id',
            'username': 'username',
            'date_joined': 'date_joined',
        }

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
                'author': ur.prepare(post.user.id),
                'body': post.content,
                # ...
            }
