.. _cookbook:

========
Cookbook
========

This is a place for community-contributed patterns & ideas for extending
Restless.


Authentication
==============

If your framework has the concept of a logged-in user (like Django), you can
do something like::

    class MyResource(DjangoResource):
        def is_authenticated(self):
            return self.request.user.is_authenticated()

