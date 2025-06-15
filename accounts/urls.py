from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView  # 외부 먼저
from .views import RegisterView, LoginView, UserView         # 내부는 그 다음

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('user/', UserView.as_view(), name='user'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]