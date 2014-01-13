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

Restless currently supports Django_ & Flask_. For the purposes of most of this
tutorial, we'll assume you're using Django. The process for developing &
interacting with the API via Flask is nearly identical (& we'll be covering the
differences at the end of this document).

There are only two steps to getting a Restless API up & functional. They are:

#. Implement a ``restless.Resource`` subclass
#. Hook up the resource to your URLs

We'll start with defining the resource subclass.

.. _Django: http://djangoproject.com/
.. _Flask: http://flask.pocoo.org/


Creating a Resource
===================


