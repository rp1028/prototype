from rest_framework import serializers
from .models import Post

class PostSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source='author.username', read_only=True)
    postId = serializers.IntegerField(source='id', read_only=True)

    class Meta:
        model = Post
        # ⭐️ fields 목록에 'image'가 포함되어 있는지 확인
        fields = ['postId', 'title', 'content', 'author', 'created_at', 'audio_file', 'image']
        read_only_fields = ['author', 'created_at']
    