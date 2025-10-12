from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, MusicLoop, Favorite


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """사용자 관리자 페이지"""
    list_display = ['email', 'username', 'nickname', 'is_active', 'is_staff', 'date_joined']
    list_filter = ['is_active', 'is_staff', 'is_superuser', 'date_joined']
    search_fields = ['email', 'username', 'nickname']
    ordering = ['-date_joined']
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('개인정보', {'fields': ('username', 'nickname', 'profile_image', 'bio')}),
        ('권한', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('중요한 날짜', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2'),
        }),
    )
    
    readonly_fields = ['date_joined', 'last_login']


@admin.register(MusicLoop)
class MusicLoopAdmin(admin.ModelAdmin):
    """음악 루프 관리자 페이지"""
    list_display = ['title', 'user', 'genre', 'bpm', 'is_public', 'play_count', 'get_favorites_count', 'created_at']
    list_filter = ['is_public', 'genre', 'created_at']
    search_fields = ['title', 'description', 'user__username', 'user__email']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('user', 'title', 'description', 'audio_file', 'thumbnail')
        }),
        ('메타데이터', {
            'fields': ('bpm', 'duration', 'genre', 'tags')
        }),
        ('설정', {
            'fields': ('is_public', 'play_count')
        }),
        ('날짜', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at', 'play_count']
    
    def get_favorites_count(self, obj):
        """좋아요 수 표시"""
        return obj.favorited_by.count()
    get_favorites_count.short_description = '좋아요 수'
    
    def get_queryset(self, request):
        """쿼리 최적화"""
        queryset = super().get_queryset(request)
        queryset = queryset.select_related('user').prefetch_related('favorited_by')
        return queryset


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """좋아요 관리자 페이지"""
    list_display = ['user', 'get_loop_title', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'user__email', 'loop__title']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    
    def get_loop_title(self, obj):
        """루프 제목 표시"""
        return obj.loop.title
    get_loop_title.short_description = '루프'
    
    def get_queryset(self, request):
        """쿼리 최적화"""
        queryset = super().get_queryset(request)
        queryset = queryset.select_related('user', 'loop')
        return queryset


# Admin 사이트 커스터마이징
admin.site.site_header = "MusicLoop 관리자"
admin.site.site_title = "MusicLoop Admin"
admin.site.index_title = "MusicLoop 관리 대시보드"
