from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    """
    객체의 소유자만 접근할 수 있도록 하는 권한 클래스
    """
    message = "이 작업을 수행할 권한이 없습니다. 본인의 콘텐츠만 접근 가능합니다."

    def has_object_permission(self, request, view, obj):
        # 객체에 user 속성이 있는지 확인
        if hasattr(obj, 'user'):
            return obj.user == request.user
        return False


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    소유자는 모든 작업 가능, 다른 사용자는 읽기만 가능
    """
    def has_object_permission(self, request, view, obj):
        # 읽기 권한은 모든 요청에 허용 (GET, HEAD, OPTIONS)
        if request.method in permissions.SAFE_METHODS:
            return True

        # 쓰기 권한은 객체의 소유자에게만 허용
        if hasattr(obj, 'user'):
            return obj.user == request.user
        return False


class IsAuthenticatedAndOwner(permissions.BasePermission):
    """
    인증된 사용자이면서 동시에 소유자인 경우만 접근 가능
    """
    message = "인증이 필요하며, 본인의 콘텐츠만 접근할 수 있습니다."

    def has_permission(self, request, view):
        # 사용자가 인증되어 있는지 확인
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # 객체의 소유자인지 확인
        if hasattr(obj, 'user'):
            return obj.user == request.user
        return False
