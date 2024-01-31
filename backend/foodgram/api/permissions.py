from rest_framework.permissions import (
    SAFE_METHODS, BasePermission, IsAuthenticatedOrReadOnly
)


class IsAuthorOrIsAdminOrReadOnly(IsAuthenticatedOrReadOnly):
    """
    Предоставляет полный доступ админу и автору,
    остальным пользователям даётся доступ только на чтение.
    """

    def has_object_permission(self, request, view, obj):
        return request.method in SAFE_METHODS or (
            request.user.is_staff or request.user == obj.author
        )


class IsAdminOrReadOnly(BasePermission):
    """
    Предоставляет полный доступ администратору,
    остальным пользователям даётся доступ только на чтение.
    """

    def has_permission(self, request, view):
        """
        Проверяет, что пользователь является администратором,
        либо метод безопасен.
        """
        return (
            request.method in SAFE_METHODS or (
                request.user.is_authenticated and request.user.is_staff
            )
        )
