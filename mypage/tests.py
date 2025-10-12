from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from .models import User, MusicLoop, Favorite
from django.core.files.uploadedfile import SimpleUploadedFile
import json


class UserModelTest(TestCase):
    """User 모델 테스트"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
    
    def test_user_creation(self):
        """사용자 생성 테스트"""
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertEqual(self.user.username, 'testuser')
        self.assertTrue(self.user.check_password('testpass123'))
    
    def test_user_str(self):
        """사용자 문자열 표현 테스트"""
        self.assertEqual(str(self.user), 'test@example.com')


class MyPageAPITest(APITestCase):
    """마이페이지 API 테스트 - 본인 정보만 접근"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123',
            nickname='테스트유저'
        )
        
        # JWT 토큰 발급
        response = self.client.post(reverse('token_obtain_pair'), {
            'email': 'test@example.com',
            'password': 'testpass123'
        })
        self.token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
    
    def test_get_profile(self):
        """프로필 조회 테스트 - 본인 정보만"""
        url = reverse('mypage:profile')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'test@example.com')
        self.assertEqual(response.data['nickname'], '테스트유저')
    
    def test_update_profile(self):
        """프로필 수정 테스트 - 본인만"""
        url = reverse('mypage:profile-update')
        data = {
            'nickname': '새로운닉네임',
            'bio': '안녕하세요!'
        }
        response = self.client.put(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['nickname'], '새로운닉네임')
        self.assertEqual(response.data['data']['bio'], '안녕하세요!')
    
    def test_change_password(self):
        """비밀번호 변경 테스트 - 본인만"""
        url = reverse('mypage:change-password')
        data = {
            'old_password': 'testpass123',
            'new_password': 'newpass123!',
            'new_password_confirm': 'newpass123!'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 새 비밀번호로 로그인 테스트
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpass123!'))
    
    def test_change_password_wrong_old_password(self):
        """잘못된 현재 비밀번호로 변경 시도"""
        url = reverse('mypage:change-password')
        data = {
            'old_password': 'wrongpass',
            'new_password': 'newpass123!',
            'new_password_confirm': 'newpass123!'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_unauthorized_access(self):
        """인증 없이 접근 시도"""
        self.client.credentials()  # 토큰 제거
        url = reverse('mypage:profile')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class MusicLoopAPITest(APITestCase):
    """음악 루프 API 테스트 - 본인의 루프만 접근"""
    
    def setUp(self):
        self.client = APIClient()
        
        # 본인 계정
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        
        # 다른 사용자 계정
        self.other_user = User.objects.create_user(
            email='other@example.com',
            username='otheruser',
            password='testpass123'
        )
        
        # JWT 토큰 발급 (본인)
        response = self.client.post(reverse('token_obtain_pair'), {
            'email': 'test@example.com',
            'password': 'testpass123'
        })
        self.token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        
        # 본인 루프 생성
        self.my_loop = MusicLoop.objects.create(
            user=self.user,
            title='My Test Loop',
            description='My Description',
            bpm=120,
            genre='Electronic'
        )
        
        # 다른 사용자의 루프 생성
        self.other_loop = MusicLoop.objects.create(
            user=self.other_user,
            title='Other User Loop',
            description='Other Description',
            bpm=140,
            genre='Rock'
        )
    
    def test_list_only_my_loops(self):
        """내 루프 목록만 조회 (다른 사용자 것 안 보임)"""
        url = reverse('mypage:myloops-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)  # 본인 것만 1개
        self.assertEqual(response.data['results'][0]['title'], 'My Test Loop')
        
        # 다른 사용자의 루프는 목록에 없어야 함
        titles = [loop['title'] for loop in response.data['results']]
        self.assertNotIn('Other User Loop', titles)
    
    def test_cannot_access_other_user_loop(self):
        """다른 사용자의 루프 접근 불가"""
        url = reverse('mypage:myloops-detail', kwargs={'pk': self.other_loop.pk})
        response = self.client.get(url)
        
        # 404 반환 (본인 것만 필터링되어 찾을 수 없음)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_get_my_loop_detail(self):
        """내 루프 조회 가능"""
        url = reverse('mypage:myloops-detail', kwargs={'pk': self.my_loop.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'My Test Loop')
        self.assertTrue(response.data['is_mine'])
    
    def test_update_my_loop(self):
        """내 루프 수정 가능"""
        url = reverse('mypage:myloops-detail', kwargs={'pk': self.my_loop.pk})
        data = {
            'title': 'Updated My Loop',
            'bpm': 130
        }
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['title'], 'Updated My Loop')
        self.assertEqual(response.data['data']['bpm'], 130)
    
    def test_cannot_update_other_user_loop(self):
        """다른 사용자의 루프 수정 불가"""
        url = reverse('mypage:myloops-detail', kwargs={'pk': self.other_loop.pk})
        data = {'title': 'Hacked Title'}
        response = self.client.patch(url, data, format='json')
        
        # 404 반환 (본인 것만 필터링되어 찾을 수 없음)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # 원본 데이터가 변경되지 않았는지 확인
        self.other_loop.refresh_from_db()
        self.assertEqual(self.other_loop.title, 'Other User Loop')
    
    def test_delete_my_loop(self):
        """내 루프 삭제 가능"""
        url = reverse('mypage:myloops-detail', kwargs={'pk': self.my_loop.pk})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(MusicLoop.objects.filter(pk=self.my_loop.pk).exists())
    
    def test_cannot_delete_other_user_loop(self):
        """다른 사용자의 루프 삭제 불가"""
        url = reverse('mypage:myloops-detail', kwargs={'pk': self.other_loop.pk})
        response = self.client.delete(url)
        
        # 404 반환 (본인 것만 필터링되어 찾을 수 없음)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # 원본 데이터가 삭제되지 않았는지 확인
        self.assertTrue(MusicLoop.objects.filter(pk=self.other_loop.pk).exists())
    
    def test_loop_statistics_only_mine(self):
        """루프 통계는 본인 것만 집계"""
        url = reverse('mypage:loops-statistics')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_loops'], 1)  # 본인 것만
    
    def test_create_loop_auto_set_user(self):
        """루프 생성 시 자동으로 본인이 작성자로 설정"""
        url = reverse('mypage:myloops-list')
        data = {
            'title': 'New Loop',
            'bpm': 125,
            'is_public': True
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # 생성된 루프의 작성자가 본인인지 확인
        loop = MusicLoop.objects.get(id=response.data['data']['id'])
        self.assertEqual(loop.user, self.user)


class FavoriteAPITest(APITestCase):
    """좋아요 API 테스트 - 본인의 좋아요만"""
    
    def setUp(self):
        self.client = APIClient()
        
        # 본인 계정
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        
        # 다른 사용자 계정
        self.other_user = User.objects.create_user(
            email='other@example.com',
            username='otheruser',
            password='testpass123'
        )
        
        # JWT 토큰 발급
        response = self.client.post(reverse('token_obtain_pair'), {
            'email': 'test@example.com',
            'password': 'testpass123'
        })
        self.token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        
        # 다른 사용자의 루프 생성
        self.loop = MusicLoop.objects.create(
            user=self.other_user,
            title='Other User Loop',
            bpm=120
        )
        
        # 본인의 루프 생성
        self.my_loop = MusicLoop.objects.create(
            user=self.user,
            title='My Loop',
            bpm=130
        )
    
    def test_toggle_favorite_add(self):
        """좋아요 추가"""
        url = reverse('mypage:favorites-toggle')
        data = {'loop_id': self.loop.id}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['is_favorited'])
        self.assertTrue(Favorite.objects.filter(user=self.user, loop=self.loop).exists())
    
    def test_toggle_favorite_remove(self):
        """좋아요 취소"""
        # 먼저 좋아요 추가
        Favorite.objects.create(user=self.user, loop=self.loop)
        
        url = reverse('mypage:favorites-toggle')
        data = {'loop_id': self.loop.id}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['is_favorited'])
        self.assertFalse(Favorite.objects.filter(user=self.user, loop=self.loop).exists())
    
    def test_cannot_favorite_own_loop(self):
        """본인의 루프에는 좋아요 불가"""
        url = reverse('mypage:favorites-toggle')
        data = {'loop_id': self.my_loop.id}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('본인의 루프', str(response.data['error']))
    
    def test_list_only_my_favorites(self):
        """본인의 좋아요 목록만 조회"""
        # 본인의 좋아요 추가
        Favorite.objects.create(user=self.user, loop=self.loop)
        
        # 다른 사용자의 좋아요 추가
        other_loop = MusicLoop.objects.create(
            user=self.other_user,
            title='Another Loop',
            bpm=140
        )
        Favorite.objects.create(user=self.other_user, loop=other_loop)
        
        url = reverse('mypage:favorites')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)  # 본인 것만
        self.assertEqual(response.data['results'][0]['loop']['title'], 'Other User Loop')
    
    def test_check_favorite_status(self):
        """좋아요 상태 확인"""
        Favorite.objects.create(user=self.user, loop=self.loop)
        
        url = reverse('mypage:favorites-check')
        response = self.client.get(url, {'loop_id': self.loop.id})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_favorited'])
    
    def test_clear_all_favorites(self):
        """모든 좋아요 삭제 - 본인 것만"""
        # 본인의 좋아요 2개 추가
        loop2 = MusicLoop.objects.create(user=self.other_user, title='Loop2', bpm=130)
        Favorite.objects.create(user=self.user, loop=self.loop)
        Favorite.objects.create(user=self.user, loop=loop2)
        
        # 다른 사용자의 좋아요
        loop3 = MusicLoop.objects.create(user=self.other_user, title='Loop3', bpm=140)
        other_favorite = Favorite.objects.create(user=self.other_user, loop=loop3)
        
        url = reverse('mypage:favorites-clear')
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['deleted_count'], 2)  # 본인 것만 2개 삭제
        
        # 본인의 좋아요는 모두 삭제됨
        self.assertEqual(Favorite.objects.filter(user=self.user).count(), 0)
        
        # 다른 사용자의 좋아요는 그대로 남아있음
        self.assertTrue(Favorite.objects.filter(id=other_favorite.id).exists())


class JWTAuthenticationTest(APITestCase):
    """JWT 인증 테스트"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
    
    def test_obtain_token(self):
        """토큰 발급 테스트"""
        url = reverse('token_obtain_pair')
        data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
    
    def test_obtain_token_invalid_credentials(self):
        """잘못된 인증 정보로 토큰 발급 시도"""
        url = reverse('token_obtain_pair')
        data = {
            'email': 'test@example.com',
            'password': 'wrongpass'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
