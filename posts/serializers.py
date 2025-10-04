from rest_framework import serializers
from .models import Post

class PostSerializer(serializers.ModelSerializer):
    postId = serializers.IntegerField(source='id', read_only=True)
    author = serializers.CharField(source='author.username', read_only=True)

    class Meta:
        model = Post
        fields = ['postId', 'title', 'content', 'author', 'created_at']
        read_only_fields = ['postId', 'author', 'created_at']