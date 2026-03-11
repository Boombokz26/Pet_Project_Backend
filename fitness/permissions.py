from rest_framework.permissions import BasePermission


class IsJWTAuthenticated(BasePermission):

    def has_permission(self, request, view):
        return request.user is not None