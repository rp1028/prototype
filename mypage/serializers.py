from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User, MusicLoop, Favorite


class UserProfileSerializer(serializers.ModelSerializer):
    """사용자 프로필 조회/수정용 Serializer - 본인 정보만"""
    loops_count = serializers.SerializerMethodField()
    favorites_count = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'nickname', 'profile_image', 
            'bio', 'date_joined', 'loops_count', 'favorites_count'
        ]
        read_only_fields = ['id', 'email', 'username', 'date_joined']

    def get_loops_count(self, obj):
        """본인이 만든 루프 개수"""
        return obj.loops.count()

    def get_favorites_count(self, obj):
        """본인이 좋아요한 루프 개수"""
        return obj.favorites.count()
    
    def validate_nickname(self, value):
        """닉네임 유효성 검사"""
        if value and len(value) < 2:
            raise serializers.ValidationError("닉네임은 최소 2자 이상이어야 합니다.")
        if value and len(value) > 50:
            raise serializers.ValidationError("닉네임은 최대 50자까지 가능합니다.")
        return value


class PasswordChangeSerializer(serializers.Serializer):
    """비밀번호 변경용 Serializer - 본인만 변경 가능"""
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True)
    new_password_confirm = serializers.CharField(required=True, write_only=True)

    def validate_old_password(self, value):
        """현재 비밀번호 검증 - 본인 확인"""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("현재 비밀번호가 올바르지 않습니다.")
        return value

    def validate(self, data):
        """새 비밀번호 검증"""
        if data['new_password'] != data['new_password_confirm']:
            raise serializers.ValidationError({
                "new_password_confirm": "새 비밀번호가 일치하지 않습니다."
            })
        
        # 새 비밀번호가 현재 비밀번호와 같은지 확인
        user = self.context['request'].user
        if user.check_password(data['new_password']):
            raise serializers.ValidationError({
                "new_password": "새 비밀번호는 현재 비밀번호와 달라야 합니다."
            })
        
        # Django의 비밀번호 유효성 검사
        validate_password(data['new_password'], self.context['request'].user)
        return data

    def save(self):
        """비밀번호 변경 저장"""
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class MusicLoopSerializer(serializers.ModelSerializer):
    """음악 루프 Serializer - 본인 것만 조회/수정"""
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_nickname = serializers.CharField(source='user.nickname', read_only=True)
    is_favorited = serializers.SerializerMethodField()
    favorites_count = serializers.SerializerMethodField()
    is_mine = serializers.SerializerMethodField()

    class Meta:
        model = MusicLoop
        fields = [
            'id', 'user_email', 'user_nickname', 'title', 'description', 
            'audio_file', 'thumbnail', 'bpm', 'duration', 'genre', 'tags', 
            'is_public', 'play_count', 'is_favorited', 'favorites_count',
            'is_mine', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user_email', 'user_nickname', 'play_count', 
                           'created_at', 'updated_at', 'is_mine']

    def get_is_favorited(self, obj):
        """현재 사용자가 좋아요했는지 여부"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Favorite.objects.filter(user=request.user, loop=obj).exists()
        return False

    def get_favorites_count(self, obj):
        """좋아요 개수"""
        return obj.favorited_by.count()
    
    def get_is_mine(self, obj):
        """내가 만든 루프인지 여부"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.user == request.user
        return False

    def validate_title(self, value):
        """제목 유효성 검사"""
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("제목을 입력해주세요.")
        if len(value) > 200:
            raise serializers.ValidationError("제목은 최대 200자까지 가능합니다.")
        return value.strip()
    
    def validate_bpm(self, value):
        """BPM 유효성 검사"""
        if value is not None:
            if value < 1 or value > 300:
                raise serializers.ValidationError("BPM은 1-300 사이의 값이어야 합니다.")
        return value


class MusicLoopCreateSerializer(serializers.ModelSerializer):
    """음악 루프 생성용 Serializer - 본인만 생성 가능"""
    class Meta:
        model = MusicLoop
        fields = [
            'title', 'description', 'audio_file', 'thumbnail',
            'bpm', 'duration', 'genre', 'tags', 'is_public'
        ]

    def validate_title(self, value):
        """제목 유효성 검사"""
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("제목을 입력해주세요.")
        if len(value) > 200:
            raise serializers.ValidationError("제목은 최대 200자까지 가능합니다.")
        return value.strip()

    def validate_audio_file(self, value):
        """오디오 파일 유효성 검사"""
        if value:
            # 파일 크기 제한 (50MB)
            if value.size > 50 * 1024 * 1024:
                raise serializers.ValidationError("오디오 파일은 최대 50MB까지 업로드 가능합니다.")
            
            # 파일 확장자 검사
            allowed_extensions = ['.mp3', '.wav', '.ogg', '.m4a', '.flac']
            if not any(value.name.lower().endswith(ext) for ext in allowed_extensions):
                raise serializers.ValidationError(
                    f"지원하는 오디오 형식: {', '.join(allowed_extensions)}"
                )
        return value

    def validate_thumbnail(self, value):
        """썸네일 이미지 유효성 검사"""
        if value:
            # 파일 크기 제한 (5MB)
            if value.size > 5 * 1024 * 1024:
                raise serializers.ValidationError("썸네일은 최대 5MB까지 업로드 가능합니다.")
            
            # 이미지 파일 확장자 검사
            allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
            if not any(value.name.lower().endswith(ext) for ext in allowed_extensions):
                raise serializers.ValidationError(
                    f"지원하는 이미지 형식: {', '.join(allowed_extensions)}"
                )
        return value

    def create(self, validated_data):
        """루프 생성 - user는 view에서 자동 설정됨"""
        # view에서 user를 설정하므로 여기서는 그대로 생성
        return super().create(validated_data)


class FavoriteSerializer(serializers.ModelSerializer):
    """좋아요 Serializer - 본인의 좋아요만"""
    loop = MusicLoopSerializer(read_only=True)

    class Meta:
        model = Favorite
        fields = ['id', 'loop', 'created_at']
        read_only_fields = ['id', 'created_at']


class SimpleUserSerializer(serializers.ModelSerializer):
    """간단한 사용자 정보 Serializer"""
    class Meta:
        model = User
        fields = ['id', 'username', 'nickname', 'profile_image']
        read_only_fields = fields
