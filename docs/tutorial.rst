.. _tutorial:

=================
Restless Tutorial
=================

Restless is an alternative take on REST frameworks. While other frameworks
attempt to be very complete, include special features or tie deeply to ORMs,
Restless is a trip back to the basics.

It is fast, lightweight, and works with a small (but growing) number of
different web frameworks. If you're interested in more of the backstory &
reasoning behind Restless, please have a gander at the :ref:`philosophy`
documentation.

You can find some complete example implementation code in `the repository`_.

.. _`the repository`: https://github.com/toastdriven/restless/tree/master/examples


Why Restless?
=============

Restless tries to be RESTful by default, but flexible enough. The main
``Resource`` class has data methods (that you implement) for all the main
RESTful actions. It also uses HTTP status codes as correctly as possible.

Restless is BYOD (bring your own data) and hence, works with almost any
ORM/data source. If you can import a module to work with the data & can
represent it as JSON, Restless can work with it.

Restless is small & easy to keep in your head. Common usages involve
overridding just a few easily remembered method names. Total source code is
a under a thousand lines of code.

Restless supports Python 3 **first**, but has backward-compatibility to work
with Python 2.6+ code. Because the future is here.

Restless is JSON-only by default. Most everything can speak JSON, it's a *data*
format (not a *document* format) & it's pleasant for both computers and humans
to work with.

Restless is well-tested.


Installation
============

Installation is a relatively simple affair. For the most recent stable release,
simply use pip_ to run::

    $ pip install restless

Alternately, you can download the latest development source from Github::

    $ git clone https://github.com/toastdriven/restless.git
    $ cd restless
    $ python setup.py install

.. _pip: http://pip-installer.org/


Getting Started
===============

Restless currently supports Django_, Flask_, Pyramid_ & Tornado_.
For the purposes of most of this
tutorial, we'll assume you're using Django. The process for developing &
interacting with the API via Flask is nearly identical (& we'll be covering the
differences at the end of this document).

There are only two steps to getting a Restless API up & functional. They are:

#. Implement a ``restless.Resource`` subclass
#. Hook up the resource to your URLs

Before beginning, you should be familiar with the common understanding of the
behavior of the various `REST methods`_.

.. _Django: http://djangoproject.com/
.. _Flask: http://flask.pocoo.org/
.. _Pyramid: http://www.pylonsproject.org/
.. _`REST methods`: http://en.wikipedia.org/wiki/Representational_state_transfer#Applied_to_web_services


About Resources
===============

The main class in Restless is :py:class:`restless.resources.Resource`. It provides
all the dispatching/authentication/deserialization/serialization/response
stuff so you don't have to.

Instead, you define/implement a handful of methods that strictly do data
access/modification. Those methods are:

* ``Resource.list`` - *GET /*
* ``Resource.detail`` - *GET /identifier/*
* ``Resource.create`` - *POST /*
* ``Resource.update`` - *PUT /identifier/*
* ``Resource.delete`` - *DELETE /identifier/*

Restless also supports some less common combinations (due to their more complex
& use-specific natures):

* ``Resource.create_detail`` - *POST /identifier/*
* ``Resource.update_list`` - *PUT /*
* ``Resource.delete_list`` - *DELETE /*

Restless includes modules for various web frameworks. To create a resource to
work with Django, you'll need to subclass from
:py:class:`restless.dj.DjangoResource`.
To create a resource to work with Flask, you'll need to subclass from
:py:class:`restless.fl.FlaskResource`.

.. note:

    The module names ``restless.dj`` & ``restless.fl`` are used (in place of
    ``restless.django`` & ``restless.flask``) to prevent import confusion.

``DjangoResource`` is itself a subclass, inheriting from
``restless.resource.Resource`` & overrides a small number of methods to make
things work smoothly.


The Existing Setup
==================

We'll assume we're creating an API for our super-awesome blog platform. We have
a ``posts`` application, which has a model setup like so...::

    # posts/models.py
    from django.contrib.auth.models import User
    from django.db import models


    class Post(models.Model):
        user = models.ForeignKey(User, related_name='posts')
        title = models.CharField(max_length=128)
        slug = models.SlugField(blank=True)
        content = models.TextField(default='', blank=True)
        posted_on = models.DateTimeField(auto_now_add=True)
        updated_on = models.DateTimeField(auto_now=True)

        class Meta(object):
            ordering = ['-posted_on', 'title']

        def __str__(self):
            return self.title

This is just enough to get the ORM going & use some real data.

The rest of the app (views, URLs, admin, forms, etc.) really aren't important
for the purposes of creating a basic Restless API, so we'll ignore them for now.


Creating A Resource
===================

We'll start with defining the resource subclass. Where you put this code isn't
particularly important (as long as other things can import the class you
define), but a great convention is ``<myapp>/api.py``. So in case of our
tutorial app, we'll place this code in a new ``posts/api.py`` file.

We'll start with the most basic functional example.::

    # posts/api.py
    from restless.dj import DjangoResource
    from restless.preparers import FieldsPreparer

    from posts.models import Post


    class PostResource(DjangoResource):

        paginate = True
        page_size = 20

        preparer = FieldsPreparer(fields={
            'id': 'id',
            'title': 'title',
            'author': 'user.username',
            'body': 'content',
            'posted_on': 'posted_on',
        })

        # GET /api/posts/ (but not hooked up yet)
        def list(self):
            return Post.objects.all()

        # GET /api/posts/<pk>/ (but not hooked up yet)
        def detail(self, pk):
            return Post.objects.get(id=pk)

As we've already covered, we're inheriting from ``restless.dj.DjangoResource``.
We're also importing our ``Post`` model, because serving data out of an API
is kinda important.

The name of the class isn't particularly important, but it should be
descriptive (and can play a role in hooking up URLs later on).

The ``paginate`` defines if the results should be paginated or not.
You can configure how many results per page setting ``page_size`` in
your resource, or using the configuring ``RESTLESS_PAGE_SIZE`` in your settings.
By default, is 10 objects per page.

Fields
------

We define a ``fields`` attribute on the class. This dictionary provides a
mapping between what the API will return & where the data is. This allows you
to mask/rename fields, prevent some fields from being exposed or lookup
information buried deep in the data model. The mapping is defined like...::

    FieldsPreparer(fields={
        'the_fieldname_exposed_to_the_user': 'a_dotted_path_to_the_data',
    })

This dotted path is what allows use to drill in. For instance, the ``author``
field above has a path of ``user.username``. When serializing, this will cause
Restless to look for an attribute (or a key on a dict) called ``user``. From
there, it will look further into the resulting object/dict looking for a
``username`` attribute/key, returning it as the final value.

Methods
-------

We're also defining a ``list`` method & a ``detail`` method. Both can take
optional positional/keyword parameters if necessary.

These methods serve the **data** to present for their given endpoints. You
don't need to manually construct any responses/status codes/etc., just provide
what data should be present.

The ``list`` method serves the ``GET`` method on the collection. It should
return a ``list`` (or similar iterable, like ``QuerySet``) of data. In this
case, we're simply returning all of our ``Post`` model instances.

The ``detail`` method also serves the ``GET`` method, but this time for single
objects **ONLY**. Providing a ``pk`` in the URL allows this method to lookup
the data that should be served.

.. note:

    Restless has this pattern of pairs of methods for each of the RESTful
    HTTP verbs, list variant & detail variant.

    ``create/create_detail`` handle ``POST``. ``update_list/update`` handle
    ``PUT``. And ``delete_list/delete`` handle ``DELETE``.


Hooking Up The URLs
===================

URLs to Restless resources get hooked up much like any other class-based view.
However, Restless's :py:class:`restless.dj.DjangoResource` comes with a
special method called ``urls``, which makes hooking up URLs more convenient.

You can hook the URLs for the resource up wherever you want. The recommended
practice would be to create a URLconf just for the API portion of your site.::

    # The ``settings.ROOT_URLCONF`` file
    # myproject/urls.py
    from django.conf.urls import url, include

    # Add this!
    from posts.api import PostResource

    urlpatterns = [
        # The usual fare, then...

        # Add this!
        url(r'api/posts/', include(PostResource.urls())),
    ]

Note that unlike some other CBVs (admin specifically), the ``urls`` here is a
**METHOD**, not an attribute/property. Those parens are important!

Manual URLconfs
---------------

You can also manually hook up URLs by specifying something like::

    urlpatterns = [
        # ...

        # Identical to the above.
        url(r'api/posts/$', PostResource.as_list(), name='api_post_list'),
        url(r'api/posts/(?P<pk>\d+)/$', PostResource.as_detail(), name='api_post_detail'),
    ]


Testing the API
===============

We've done enough to get the API (provided there's data in the DB) going, so
let's make some requests!

Go to a terminal & run::

    $ curl -X GET http://127.0.0.1:8000/api/posts/

You should get something like this back...::

    {
        "objects": [
            {
                "id": 1,
                "title": "First Post!",
                "author": "daniel",
                "body": "This is the very first post on my shiny-new blog platform...",
                "posted_on": "2014-01-12T15:23:46",
            },
            {
                # More here...
            }
        ]
    }

You can also go to the same URL in a browser (http://127.0.0.1:8000/api/posts/)
& you should also get the JSON back.

.. note:

    Consider using browser plugins like JSONView to nicely format the JSON.

    You can get nice formatting at the command line by either piping to
    ``curl -X GET http://127.0.0.1:8000/api/posts/ | python -m json.tool``.
    Alternatively, you can use a tool like httpie_
    (``http http://127.0.0.1:8000/api/posts/``).

.. _httpie: https://pypi.python.org/pypi/httpie

You can then load up an individual object by changing the URL to include a
``pk``.::

    $ curl -X GET http://127.0.0.1:8000/api/posts/1/

You should get back...::

    {
        "id": 1,
        "title": "First Post!",
        "author": "daniel",
        "body": "This is the very first post on my shiny-new blog platform...",
        "posted_on": "2014-01-12T15:23:46",
    }

Note that the ``objects`` wrapper is no longer present & we get back the JSON
for just that single object. Hooray!


Creating/Updating/Deleting Data
===============================

A read-only API is nice & all, but sometimes you want to be able to create data
as well. So we'll implement some more methods.::

    # posts/api.py
    from restless.dj import DjangoResource
    from restless.preparers import FieldsPreparer

    from posts.models import Post


    class PostResource(DjangoResource):
        preparer = FieldsPreparer(fields={
            'id': 'id',
            'title': 'title',
            'author': 'user.username',
            'body': 'content',
            'posted_on': 'posted_on',
        })

        # GET /api/posts/
        def list(self):
            return Post.objects.all()

        # GET /api/posts/<pk>/
        def detail(self, pk):
            return Post.objects.get(id=pk)

        # Add this!
        # POST /api/posts/
        def create(self):
            return Post.objects.create(
                title=self.data['title'],
                user=User.objects.get(username=self.data['author']),
                content=self.data['body']
            )

        # Add this!
        # PUT /api/posts/<pk>/
        def update(self, pk):
            try:
                post = Post.objects.get(id=pk)
            except Post.DoesNotExist:
                post = Post()

            post.title = self.data['title']
            post.user = User.objects.get(username=self.data['author'])
            post.content = self.data['body']
            post.save()
            return post

        # Add this!
        # DELETE /api/posts/<pk>/
        def delete(self, pk):
            Post.objects.get(id=pk).delete()

By adding the ``create/update/delete`` methods, we now have the ability to
add new items, update existing ones & delete individual items. Most of this
code is relatively straightforward ORM calls, but there are a few interesting
new things going on here.

Note that the ``create`` & ``update`` methods are both using a special
``self.data`` variable. This is created by Restless during deserialization &
is the **JSON** data the user sends as part of the request.

.. warning::

    This data (within ``self.data``) is mostly unsanitized (beyond standard
    JSON decoding) & could contain anything (not just the ``fields`` you
    define).

    You know your data best & validation is **very** non-standard between
    frameworks, so this is a place where Restless punts.

    Some people like cleaning the data with ``Forms``, others prefer to
    hand-sanitize, some do model validation, etc. Do what works best for you.

    You can refer to the :ref:`extending` documentation for recommended
    approaches.

Also note that ``delete`` is the first method with **no return value**. You
can do the same thing on ``create/update`` if you like. When there's no
meaningful data returned, Restless simply sends back a correct status code
& an empty body.

Finally, there's no need to hook up more URLconfs. Restless delegates based
on a list & a detail endpoint. All further dispatching is HTTP verb-based &
handled by Restless.


Testing the API, Round 2
========================

Now let's test out our new functionality! Go to a terminal & run::

    $ curl -X POST -H "Content-Type: application/json" -d '{"title": "New library released!", "author": "daniel", "body": "I just released a new thing!"}' http://127.0.0.1:8000/api/posts/

You should get something like this back...::

    {
        "error": "Unauthorized"
    }

Wait, what?!! But we added our new methods & everything!

The reason you get unauthorized is that by default, **only GET** requests are
allowed by Restless. It's the only sane/safe default to have & it's very easy
to fix.


Error Handling
==============

By default, Restless tries to serialize any exceptions that may be encountered.
What gets serialized depends on two methods: ``Resource.is_debug()`` &
``Resource.bubble_exceptions()``.

``is_debug``
------------

Regardless of the error type, the exception's message will get serialized into
the response under the ``"error"`` key. For example, if an ``IOError`` is
raised during processing, you'll get a response like::

    HTTP/1.0 500 INTERNAL SERVER ERROR
    Content-Type: application/json
    # Other headers...

    {
        "error": "Whatever."
    }

If ``Resource.is_debug()`` returns ``True`` (the default is ``False``), Restless
will also include a traceback. For example::

    HTTP/1.0 500 INTERNAL SERVER ERROR
    Content-Type: application/json
    # Other headers...

    {
        "error": "Whatever.",
        "traceback": "Traceback (most recent call last):\n # Typical traceback..."
    }

Each framework-specific ``Resource`` subclass implements ``is_debug()`` in a
way most appropriate for the framework. In the case of the ``DjangoResource``,
it returns ``settings.DEBUG``, allowing your resources to stay consistent with
the rest of your application.

``bubble_exceptions``
---------------------

If ``Resource.bubble_exceptions()`` returns ``True`` (the default is ``False``),
any exception encountered will simply be re-raised & it's up to your setup to
handle it. Typically, this behavior is undesirable except in development & with
frameworks that can provide extra information/debugging on exceptions. Feel
free to override it (``return True``) or implement application-specific logic
if that meets your needs.


Authentication
==============

We're going to override one more method in our resource subclass, this time
adding the ``is_authenticated`` method.::

    # posts/api.py
    from restless.dj import DjangoResource
    from restless.preparers import FieldsPreparer

    from posts.models import Post


    class PostResource(DjangoResource):
        preparer = FieldsPreparer(fields={
            'id': 'id',
            'title': 'title',
            'author': 'user.username',
            'body': 'content',
            'posted_on': 'posted_on',
        }

        # Add this!
        def is_authenticated(self):
            # Open everything wide!
            # DANGEROUS, DO NOT DO IN PRODUCTION.
            return True

            # Alternatively, if the user is logged into the site...
            # return self.request.user.is_authenticated()

            # Alternatively, you could check an API key. (Need a model for this...)
            # from myapp.models import ApiKey
            # try:
            #     key = ApiKey.objects.get(key=self.request.GET.get('api_key'))
            #     return True
            # except ApiKey.DoesNotExist:
            #     return False

        def list(self):
            return Post.objects.all()

        def detail(self, pk):
            return Post.objects.get(id=pk)

        def create(self):
            return Post.objects.create(
                title=self.data['title'],
                user=User.objects.get(username=self.data['author']),
                content=self.data['body']
            )

        def update(self, pk):
            try:
                post = Post.objects.get(id=pk)
            except Post.DoesNotExist:
                post = Post()

            post.title = self.data['title']
            post.user = User.objects.get(username=self.data['author'])
            post.content = self.data['body']
            post.save()
            return post

        def delete(self, pk):
            Post.objects.get(id=pk).delete()

With that change in place, now our API should play nice...


Testing the API, Round 3
========================

Back to the terminal & again run::

    $ curl -X POST -H "Content-Type: application/json" -d '{"title": "New library released!", "author": "daniel", "body": "I just released a new thing!"}' http://127.0.0.1:8000/api/posts/

You should get something like this back...::

    {
        "body": "I just released a new thing!",
        "title": "New library released!",
        "id": 3,
        "posted_on": "2014-01-13T10:02:55.926857+00:00",
        "author": "daniel"
    }

Hooray! Now we can check for it in the list view
(``GET`` http://127.0.0.1:8000/api/posts/) or by a detail (``GET``
http://127.0.0.1:8000/api/posts/3/).

We can also update it. Restless expects **complete** bodies (don't try to send
partial updates, that's typically reserved for ``PATCH``).::

    $ curl -X PUT -H "Content-Type: application/json" -d '{"title": "Another new library released!", "author": "daniel", "body": "I just released a new piece of software!"}' http://127.0.0.1:8000/api/posts/3/

And we can delete our new data if we decide we don't like it.::

    $ curl -X DELETE http://127.0.0.1:8000/api/posts/3/


Conclusion
==========

We've now got a basic, working RESTful API in a short amount of code! And
the possibilities don't stop at the ORM. You could hook up:

* Redis
* the NoSQL flavor of the month
* text/log files
* wrap calls to other (nastier) APIs

You may also want to check the :ref:`cookbook` for other interesting/useful
possibilities & implementation patterns.


Bonus: Flask Support
====================

Outside of the ORM, precious little of what we implemented above was
Django-specific. If you used an ORM like `Peewee`_ or `SQLAlchemy`_, you'd have
very similar-looking code.

In actuality, there are just two changes to make the Restless-portion of the
above work within Flask.

#. Change the inheritance
#. Change how the URL routes are hooked up.

.. _Peewee: http://peewee.readthedocs.org/en/latest/
.. _SQLAlchemy: http://www.sqlalchemy.org/


Change The Inheritance
----------------------

Restless ships with a :py:class:`restless.fl.FlaskResource` class, akin to the
``DjangoResource``. So the first change is dead simple.::

    # Was: from restless.dj import DjangoResource
    # Becomes:
    from restless.fl import FlaskResource

    # ...

    # Was: class PostResource(DjangoResource):
    # Becomes:
    class PostResource(FlaskResource):
        # ...


Change How The URL Routes Are Hooked Up
---------------------------------------

Again, similar to the ``DjangoResource``, the ``FlaskResource`` comes with a
special method to make hooking up the routes easier.

Wherever your ``PostResource`` is defined, import your Flask ``app``, then call
the following::

    PostResource.add_url_rules(app, rule_prefix='/api/posts/')

This will hook up the same two endpoints (list & detail, just like Django above)
within the Flask app, doing similar dispatches.

You can also do this manually (but it's ugly/hurts).::

    app.add_url_rule('/api/posts/', endpoint='api_posts_list', view_func=PostResource.as_list(), methods=['GET', 'POST', 'PUT', 'DELETE'])
    app.add_url_rule('/api/posts/<pk>/', endpoint='api_posts_detail', view_func=PostResource.as_detail(), methods=['GET', 'POST', 'PUT', 'DELETE'])

Done!
-----

Believe it or not, if your ORM could be made to look similar, that's all the
further changes needed to get the same API (with the same end-user interactions)
working on Flask! Huzzah!
