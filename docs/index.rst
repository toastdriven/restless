========
restless
========

A lightweight REST miniframework for Python.

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


Topics
======

.. toctree::
   :maxdepth: 2

   tutorial
   philosophy

   extending

.. toctree::
   :maxdepth: 1

   cookbook

   contributing
   security


API Reference
=============

.. toctree::
   :glob:

   reference/*


Release Notes
=============

.. toctree::
   :maxdepth: 1

   releasenotes/v1.4.0
   releasenotes/v1.3.0
   releasenotes/v1.2.0
   releasenotes/v1.1.0
   releasenotes/v1.0.0


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

