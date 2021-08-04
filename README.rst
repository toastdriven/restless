========
restless
========

.. image:: https://travis-ci.org/toastdriven/restless.svg?branch=master
    :target: https://travis-ci.org/toastdriven/restless

.. image:: https://coveralls.io/repos/github/toastdriven/restless/badge.svg?branch=master
   :target: https://coveralls.io/github/toastdriven/restless?branch=master


A lightweight REST miniframework for Python.

Documentation is at https://restless.readthedocs.io/.

Works great with Django_, Flask_, Pyramid_, Tornado_ & Itty_, but should be useful for
many other Python web frameworks. Based on the lessons learned from Tastypie_
& other REST libraries.

.. _Django: https://www.djangoproject.com/
.. _Flask: http://flask.pocoo.org/
.. _Pyramid: https://pylonsproject.org/
.. _Itty: https://pypi.org/project/itty/
.. _Tastypie: http://tastypieapi.org/
.. _Tornado: https://www.tornadoweb.org/
.. _tox: https://tox.readthedocs.io/


Features
========

* Small, fast codebase
* JSON output by default, but overridable
* RESTful
* Python 3.6+
* Django 2.2+
* Flexible


Anti-Features
=============

(Things that will never be added...)

* Automatic ORM integration
* Authorization (per-object or not)
* Extensive filtering options
* XML output (though you can implement your own)
* Metaclasses
* Mixins
* HATEOAS


Why?
====

Quite simply, I care about creating flexible & RESTFul APIs. In building
Tastypie, I tried to create something extremely complete & comprehensive.
The result was writing a lot of hook methods (for easy extensibility) & a lot
of (perceived) bloat, as I tried to accommodate for everything people might
want/need in a flexible/overridable manner.

But in reality, all I really ever personally want are the RESTful verbs, JSON
serialization & the ability of override behavior.

This one is written for me, but maybe it's useful to you.


Manifesto
=========

Rather than try to build something that automatically does the typically
correct thing within each of the views, it's up to you to implement the bodies
of various HTTP methods.

Example code:

.. code:: python

    # posts/api.py
    from django.contrib.auth.models import User

    from restless.dj import DjangoResource
    from restless.preparers import FieldsPreparer

    from posts.models import Post


    class PostResource(DjangoResource):
        # Controls what data is included in the serialized output.
        preparer = FieldsPreparer(fields={
            'id': 'id',
            'title': 'title',
            'author': 'user.username',
            'body': 'content',
            'posted_on': 'posted_on',
        })

        # GET /
        def list(self):
            return Post.objects.all()

        # GET /pk/
        def detail(self, pk):
            return Post.objects.get(id=pk)

        # POST /
        def create(self):
            return Post.objects.create(
                title=self.data['title'],
                user=User.objects.get(username=self.data['author']),
                content=self.data['body']
            )

        # PUT /pk/
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

        # DELETE /pk/
        def delete(self, pk):
            Post.objects.get(id=pk).delete()

Hooking it up:

.. code:: python

    # api/urls.py
    from django.conf.urls.default import url, include

    from posts.api import PostResource

    urlpatterns = [
        # The usual suspects, then...

        url(r'^api/posts/', include(PostResource.urls())),
    ]


Licence
=======

BSD


Running the Tests
=================

The test suite uses tox_ for simultaneous support of multiple versions of both
Python and Django. The current versions of Python supported are:

* CPython 3.6
* CPython 3.7
* CPython 3.8
* CPython 3.9
* PyPy

You just need to install the Python interpreters above and the `tox` package
(available via `pip`), then run the `tox` command.
