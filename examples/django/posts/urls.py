from django.conf.urls import url, include

from .api import PostResource


urlpatterns = [
    url(r'^posts/', include(PostResource.urls())),

    # Alternatively, if you don't like the defaults...
    # url(r'^posts/$', PostResource.as_list(), name='api_posts_list'),
    # url(r'^posts/(?P<pk>\d+)/$', PostResource.as_detail(), name='api_posts_detail'),
]
