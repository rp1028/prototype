from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MyPageViewSet, MyLoopsViewSet, MyFavoritesViewSet

router = DefaultRouter()
router.register(r'myloops', MyLoopsViewSet, basename='myloops')

app_name = 'mypage'

urlpatterns = [
    # ============== 마이페이지 프로필 관련 (본인만) ==============
    path('profile/', MyPageViewSet.as_view({'get': 'profile'}), name='profile'),
    path('profile/update/', MyPageViewSet.as_view({'put': 'update_profile', 'patch': 'update_profile'}), name='profile-update'),
    path('profile/password/', MyPageViewSet.as_view({'post': 'change_password'}), name='change-password'),
    path('profile/image/upload/', MyPageViewSet.as_view({'post': 'upload_profile_image'}), name='upload-profile-image'),
    path('profile/image/delete/', MyPageViewSet.as_view({'delete': 'delete_profile_image'}), name='delete-profile-image'),
    
    # ============== 내 루프 관련 (본인 것만 CRUD) ==============
    # router로 자동 생성되는 URL:
    # GET    /api/mypage/myloops/              - 내 루프 목록
    # POST   /api/mypage/myloops/              - 새 루프 생성
    # GET    /api/mypage/myloops/{id}/         - 내 특정 루프 조회
    # PUT    /api/mypage/myloops/{id}/         - 내 루프 수정
    # PATCH  /api/mypage/myloops/{id}/         - 내 루프 부분 수정
    # DELETE /api/mypage/myloops/{id}/         - 내 루프 삭제
    path('', include(router.urls)),
    
    # 추가 루프 관련 엔드포인트
    path('loops/statistics/', MyLoopsViewSet.as_view({'get': 'statistics'}), name='loops-statistics'),
    
    # ============== 좋아요 관련 (본인의 좋아요만) ==============
    path('favorites/', MyFavoritesViewSet.as_view({'get': 'list'}), name='favorites'),
    path('favorites/toggle/', MyFavoritesViewSet.as_view({'post': 'toggle'}), name='favorites-toggle'),
    path('favorites/check/', MyFavoritesViewSet.as_view({'get': 'check'}), name='favorites-check'),
    path('favorites/clear/', MyFavoritesViewSet.as_view({'delete': 'clear_all'}), name='favorites-clear'),
]
