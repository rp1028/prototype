from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.db.models import Q
from django.shortcuts import get_object_or_404

from .models import User, MusicLoop, Favorite
from .serializers import (
    UserProfileSerializer, 
    PasswordChangeSerializer,
    MusicLoopSerializer,
    MusicLoopCreateSerializer,
    FavoriteSerializer
)
from .permissions import IsOwner, IsAuthenticatedAndOwner


class MyPageViewSet(viewsets.ViewSet):
    """마이페이지 관련 ViewSet - 본인 정보만 접근 가능"""
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    @action(detail=False, methods=['get'])
    def profile(self, request):
        """내 프로필 조회 - 본인 정보만 조회"""
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['put', 'patch'])
    def update_profile(self, request):
        """프로필 수정 - 본인 정보만 수정 가능"""
        serializer = UserProfileSerializer(
            request.user, 
            data=request.data, 
            partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': '프로필이 성공적으로 수정되었습니다.',
                'data': serializer.data
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def change_password(self, request):
        """비밀번호 변경 - 본인만 가능"""
        serializer = PasswordChangeSerializer(
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': '비밀번호가 성공적으로 변경되었습니다.'
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def upload_profile_image(self, request):
        """프로필 이미지 업로드 - 본인만 가능"""
        if 'profile_image' not in request.FILES:
            return Response(
                {'error': '프로필 이미지를 업로드해주세요.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = request.user
        # 기존 이미지가 있으면 삭제
        if user.profile_image:
            user.profile_image.delete(save=False)
        
        user.profile_image = request.FILES['profile_image']
        user.save()
        
        serializer = UserProfileSerializer(user)
        return Response({
            'message': '프로필 이미지가 업로드되었습니다.',
            'data': serializer.data
        })

    @action(detail=False, methods=['delete'])
    def delete_profile_image(self, request):
        """프로필 이미지 삭제 - 본인만 가능"""
        user = request.user
        if user.profile_image:
            user.profile_image.delete()
            user.save()
            return Response(
                {'message': '프로필 이미지가 삭제되었습니다.'},
                status=status.HTTP_200_OK
            )
        return Response(
            {'message': '삭제할 프로필 이미지가 없습니다.'},
            status=status.HTTP_404_NOT_FOUND
        )


class MyLoopsViewSet(viewsets.ModelViewSet):
    """내 음악 루프 관련 ViewSet - 본인의 루프만 접근 가능"""
    permission_classes = [IsAuthenticated, IsOwner]
    serializer_class = MusicLoopSerializer
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        """현재 로그인한 사용자의 루프만 반환"""
        # 중요: 본인의 루프만 필터링
        return MusicLoop.objects.filter(user=self.request.user).order_by('-created_at')

    def get_serializer_class(self):
        if self.action == 'create':
            return MusicLoopCreateSerializer
        return MusicLoopSerializer

    def list(self, request, *args, **kwargs):
        """내 루프 목록 조회 - 본인 것만"""
        queryset = self.get_queryset()
        
        # 추가 필터링 옵션
        is_public = request.query_params.get('is_public', None)
        genre = request.query_params.get('genre', None)
        search = request.query_params.get('search', None)
        
        if is_public is not None:
            queryset = queryset.filter(is_public=is_public.lower() == 'true')
        
        if genre:
            queryset = queryset.filter(genre__icontains=genre)
        
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | 
                Q(description__icontains=search)
            )
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'count': queryset.count(),
            'results': serializer.data
        })

    def retrieve(self, request, *args, **kwargs):
        """특정 루프 조회 - 본인 것만"""
        instance = self.get_object()  # 이미 get_queryset()으로 본인 것만 필터링됨
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        """루프 생성 - 자동으로 본인이 작성자로 설정됨"""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            # 자동으로 현재 사용자를 작성자로 설정
            loop = serializer.save(user=request.user)
            return Response(
                {
                    'message': '루프가 성공적으로 생성되었습니다.',
                    'data': MusicLoopSerializer(loop, context={'request': request}).data
                },
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        """루프 수정 - 본인 것만 수정 가능"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # 이중 체크: 본인의 루프인지 확인
        if instance.user != request.user:
            return Response(
                {'error': '본인의 루프만 수정할 수 있습니다.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': '루프가 성공적으로 수정되었습니다.',
                'data': serializer.data
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, *args, **kwargs):
        """루프 부분 수정 - 본인 것만"""
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """루프 삭제 - 본인 것만 삭제 가능"""
        instance = self.get_object()
        
        # 이중 체크: 본인의 루프인지 확인
        if instance.user != request.user:
            return Response(
                {'error': '본인의 루프만 삭제할 수 있습니다.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        loop_title = instance.title
        instance.delete()
        return Response(
            {'message': f'"{loop_title}" 루프가 삭제되었습니다.'},
            status=status.HTTP_204_NO_CONTENT
        )

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """내 루프 통계 - 본인 것만"""
        loops = self.get_queryset()  # 이미 본인 것만 필터링됨
        total_loops = loops.count()
        total_plays = sum(loop.play_count for loop in loops)
        total_favorites = sum(loop.favorited_by.count() for loop in loops)

        return Response({
            'total_loops': total_loops,
            'total_plays': total_plays,
            'total_favorites': total_favorites,
            'public_loops': loops.filter(is_public=True).count(),
            'private_loops': loops.filter(is_public=False).count(),
        })

    @action(detail=True, methods=['post'])
    def increment_play_count(self, request, pk=None):
        """재생수 증가 - 본인 루프만"""
        loop = self.get_object()
        loop.play_count += 1
        loop.save()
        return Response({
            'message': '재생수가 증가되었습니다.',
            'play_count': loop.play_count
        })


class MyFavoritesViewSet(viewsets.ViewSet):
    """좋아요한 루프 관련 ViewSet - 본인의 좋아요만"""
    permission_classes = [IsAuthenticated]

    def list(self, request):
        """좋아요한 루프 목록 - 본인이 좋아요한 것만"""
        favorites = Favorite.objects.filter(
            user=request.user
        ).select_related('loop', 'loop__user').order_by('-created_at')
        
        # 검색 기능
        search = request.query_params.get('search', None)
        if search:
            favorites = favorites.filter(
                Q(loop__title__icontains=search) |
                Q(loop__description__icontains=search)
            )
        
        serializer = FavoriteSerializer(favorites, many=True, context={'request': request})
        return Response({
            'count': favorites.count(),
            'results': serializer.data
        })

    @action(detail=False, methods=['post'])
    def toggle(self, request):
        """좋아요 토글 (추가/제거) - 본인만 가능"""
        loop_id = request.data.get('loop_id')
        
        if not loop_id:
            return Response(
                {'error': 'loop_id가 필요합니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            loop = MusicLoop.objects.get(id=loop_id)
        except MusicLoop.DoesNotExist:
            return Response(
                {'error': '루프를 찾을 수 없습니다.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # 본인의 루프에는 좋아요 불가 (선택 사항)
        if loop.user == request.user:
            return Response(
                {'error': '본인의 루프에는 좋아요를 할 수 없습니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        favorite, created = Favorite.objects.get_or_create(
            user=request.user,
            loop=loop
        )

        if not created:
            favorite.delete()
            return Response({
                'message': '좋아요가 취소되었습니다.',
                'is_favorited': False
            })
        
        return Response({
            'message': '좋아요가 추가되었습니다.',
            'is_favorited': True
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def check(self, request):
        """특정 루프의 좋아요 상태 확인 - 본인만"""
        loop_id = request.query_params.get('loop_id')
        
        if not loop_id:
            return Response(
                {'error': 'loop_id가 필요합니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        is_favorited = Favorite.objects.filter(
            user=request.user,
            loop_id=loop_id
        ).exists()
        
        return Response({
            'loop_id': loop_id,
            'is_favorited': is_favorited
        })

    @action(detail=False, methods=['delete'])
    def clear_all(self, request):
        """모든 좋아요 삭제 - 본인 것만"""
        deleted_count, _ = Favorite.objects.filter(user=request.user).delete()
        return Response({
            'message': f'{deleted_count}개의 좋아요가 삭제되었습니다.',
            'deleted_count': deleted_count
        })
