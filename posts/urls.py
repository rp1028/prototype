from django.urls import path
from posts.views import PostCreateView
from posts.views import PostListView
urlpatterns = [
    path('create-post/', PostCreateView.as_view(), name='create-post'),
    path('list-posts/', PostListView.as_view(), name='list-posts'),  
]