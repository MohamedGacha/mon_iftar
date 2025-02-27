from rest_framework import permissions

from .models import Benevole


class IsAdminUser(permissions.BasePermission):
    """Custom permission to only allow admin users to create a bénévole."""

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.admin


class IsRegularUser(permissions.BasePermission):
    """
    Allows access only to users who are not in their first login.
    """

    def has_permission(self, request, view):
        user = request.user

        # Ensure the user is authenticated and is a Benevole instance
        if not request.user.is_authenticated or not isinstance(user, Benevole):
            return False

        # Check if the user is not in the first login state
        return not user.is_first_loggin


class IsFirstLoginUser(permissions.BasePermission):
    """
    Allows access only to users who are on their first login.
    """

    def has_permission(self, request, view):
        user = request.user

        # Ensure the user is authenticated and is a Benevole instance
        if not request.user.is_authenticated or not isinstance(user, Benevole):
            return False

        # Check if the user is in the first login state
        return user.is_first_loggin
