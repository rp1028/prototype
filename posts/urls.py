from django.urls import path
from .views import PostCreateView

urlpatterns = [
    path('create-post/', PostCreateView.as_view(), name='create-post'),
]