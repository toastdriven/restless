from django.urls import path, include

from .api import PostResource


urlpatterns = [
    path('posts/', include(PostResource.urls())),

    # Alternatively, if you don't like the defaults...
    # path('posts/', PostResource.as_list(), name='api_posts_list'),
    # path('posts/<pk>/', PostResource.as_detail(), name='api_posts_detail'),
]
