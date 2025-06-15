# accounts/views.py

from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User


class RegisterView(APIView):
    def post(self, request):
        username = request.data.get('username')  # 이메일로 들어옴
        password = request.data.get('password')
        nickname = request.data.get('nickname')  # 추가된 필드

        if User.objects.filter(username=username).exists():
            return Response({'error': '이미 존재하는 사용자입니다.'}, status=400)

        user = User.objects.create_user(username=username, password=password)
        user.first_name = nickname  # 또는 별도 필드 추가했다면 user.nickname = ...
        user.save()

        return Response({'message': '회원가입 성공'}, status=201)
    
class LoginView(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        

        user = authenticate(username=username, password=password)
        if user is None:
            return Response({'error': '인증 실패'}, status=401)

        refresh = RefreshToken.for_user(user)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        })


class UserView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response({
            'username': request.user.username,
            'id': request.user.id
        })
