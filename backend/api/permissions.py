from rest_framework import permissions


class IsAuthorOrReadOnly(permissions.BasePermission):
    """
    Разрешает редактирование объекта только его автору.

    Для безопасных методов (GET, HEAD, OPTIONS) доступ открыт всем.
    Для остальных методов доступ разрешён только автору объекта.
    """

    def has_object_permission(self, request, view, obj):
        return (
            request.method in permissions.SAFE_METHODS
            or obj.author == request.user
        )
