from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('이메일은 필수입니다')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True, verbose_name='이메일')
    username = models.CharField(max_length=50, unique=True, verbose_name='사용자명')
    nickname = models.CharField(max_length=50, blank=True, verbose_name='닉네임')
    profile_image = models.ImageField(upload_to='profiles/', blank=True, null=True, verbose_name='프로필 이미지')
    bio = models.TextField(blank=True, verbose_name='자기소개')
    
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now, verbose_name='가입일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        db_table = 'users'
        verbose_name = '사용자'
        verbose_name_plural = '사용자들'

    def __str__(self):
        return self.email


class MusicLoop(models.Model):
    """음악 루프 모델"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='loops', verbose_name='작성자')
    title = models.CharField(max_length=200, verbose_name='제목')
    description = models.TextField(blank=True, verbose_name='설명')
    audio_file = models.FileField(upload_to='loops/', verbose_name='오디오 파일')
    thumbnail = models.ImageField(upload_to='thumbnails/', blank=True, null=True, verbose_name='썸네일')
    
    bpm = models.IntegerField(null=True, blank=True, verbose_name='BPM')
    duration = models.FloatField(null=True, blank=True, verbose_name='재생시간(초)')
    genre = models.CharField(max_length=50, blank=True, verbose_name='장르')
    tags = models.JSONField(default=list, blank=True, verbose_name='태그')
    
    is_public = models.BooleanField(default=True, verbose_name='공개여부')
    play_count = models.IntegerField(default=0, verbose_name='재생수')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')

    class Meta:
        db_table = 'music_loops'
        verbose_name = '음악 루프'
        verbose_name_plural = '음악 루프들'
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class Favorite(models.Model):
    """좋아요 모델"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites', verbose_name='사용자')
    loop = models.ForeignKey(MusicLoop, on_delete=models.CASCADE, related_name='favorited_by', verbose_name='루프')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')

    class Meta:
        db_table = 'favorites'
        verbose_name = '좋아요'
        verbose_name_plural = '좋아요들'
        unique_together = ('user', 'loop')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.loop.title}"
