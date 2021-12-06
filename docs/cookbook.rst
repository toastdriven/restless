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

If you need a more fine graned authentication you could check your current endpoint and do something like that::

    class MyResource(DjangoResource):
        def is_authenticated(self):
            if self.endpoint in ('update', 'create'):
                return self.request.user.is_authenticated()
            else:
                return True


Example with Django
===================

This is an example of an endpoint for a model Book::

    from restless.dj import DjangoResource
    from restless.preparers import FieldsPreparer

    from .models import Book

    class BookResource(DjangoResource):
        preparer = FieldsPreparer(fields={
            'book_author': 'author.name',
            'book_title': 'title',
            'book_pages': 'pages',
        })

        def list(self):
          return Book.objects.all()

        def detail(self, pk):
           return Book.objects.get(id=pk)
          
        def create(self):
            return Book.objects.create(
                author=Author.objects.get(name=self.data['author']),
                title=self.data['title'],
                pages=self.data['pages']
            )
        
        def update(self, pk):
            book = Book.objects.get(id=pk)
            book.author = Author.objects.get(name=self.data['author'])
            book.title = self.data['title']
            book.pages = self.data['pages']
            book.save
            return book


    # On the urls.py...
    from django.conf.urls import include, path
    from .api import BookResource

    urlpatterns = [
        path(r'books/', include(BookResource.urls())),
    ]


Using serializer
================

How to use restless without preparers. The methods must return a dict:: 

    from restless.resources import Resource
    from restless.serializers import JSONSerializer

    class MyResource(Resource):
        serializer = JSONSerializer()

        def detail(self, pk):
            return {'pk': pk}
