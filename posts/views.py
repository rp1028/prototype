from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.filters import OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from .serializers import PostSerializer
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Post

class PostCreateView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        serializer = PostSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(author=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class PostListView(ListAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    filter_backends = [OrderingFilter]
    ordering_fields = ['created_at', 'title']
    ordering = ['-created_at'] 

    # ⭐️ --- 추가할 코드 시작 --- ⭐️
class PostUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, post_id):
        """게시글 수정을 위해 기존 데이터를 불러옵니다."""
        try:
            post = Post.objects.get(id=post_id)
            # 본인이 쓴 글이 아니면 수정 페이지에 들어갈 수 없습니다.
            if post.author != request.user:
                return Response({'error': '수정 권한이 없습니다.'}, status=status.HTTP_403_FORBIDDEN)
            serializer = PostSerializer(post)
            return Response(serializer.data)
        except Post.DoesNotExist:
            return Response({'error': '게시글을 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, post_id):
        """수정된 내용을 데이터베이스에 저장합니다."""
        try:
            post = Post.objects.get(id=post_id)
            if post.author != request.user:
                return Response({'error': '수정 권한이 없습니다.'}, status=status.HTTP_403_FORBIDDEN)
            
            serializer = PostSerializer(post, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Post.DoesNotExist:
            return Response({'error': '게시글을 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
# ⭐️ --- 추가할 코드 끝 --- ⭐️

class PostDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, post_id):
        try:
            post = Post.objects.get(id=post_id)
            # 작성자 또는 관리자만 삭제 가능
            if (post.author != request.user) and (not request.user.is_staff) and (not request.user.is_superuser):
                return Response({'error': '삭제 권한이 없습니다.'}, status=status.HTTP_403_FORBIDDEN)
            post.delete()
            return Response({'message': '게시글이 삭제되었습니다.'}, status=status.HTTP_200_OK)
        except Post.DoesNotExist:
            return Response({'error': '게시글을 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
        