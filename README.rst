========
restless
========

.. image:: https://travis-ci.org/toastdriven/restless.png?branch=master
        :target: https://travis-ci.org/toastdriven/restless

A lightweight REST miniframework for Python.

Documentation is at http://restless.readthedocs.org/.

Works great with Django_, Flask_, Pyramid_ & Itty_, but should be useful for
many other Python web frameworks. Based on the lessons learned from Tastypie_
& other REST libraries.

.. _Django: http://djangoproject.com/
.. _Flask: http://flask.pocoo.org/
.. _Pyramid: http://www.pylonsproject.org/
.. _Itty: https://pypi.python.org/pypi/itty
.. _Tastypie: http://tastypieapi.org/


Features
========

* Small, fast codebase
* JSON output by default, but overridable
* RESTful
* Python 3.3+ (with shims to make broke-ass Python 2.6+ work)
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

    from posts.models import Post


    class PostResource(DjangoResource):
        # Controls what data is included in the serialized output.
        preparer = Preparer(fields={
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
    from django.conf.urls.default import url, patterns, include

    from posts.api import PostResource

    urlpatterns = patterns('',
        # The usual suspects, then...

        url(r'^api/posts/', include(PostResource.urls())),
    )


Licence
=======

BSD


Running the Tests
=================

Getting the tests running looks like:

.. code:: sh

    $ virtualenv -p python3 env3
    $ . env3/bin/activate
    $ pip install -r test3_requirements.txt
    $ export PYTHONPATH=`pwd`
    $ py.test -s -v --cov=restless --cov-report=html tests

For Python 2:

.. code:: sh

    $ virtualenv env2
    $ . env2/bin/activate
    $ pip install -r test2_requirements.txt
    $ export PYTHONPATH=`pwd`
    $ py.test -s -v --cov=restless --cov-report=html tests

Coverage is at about 94%, so please don't make it worse. :D
