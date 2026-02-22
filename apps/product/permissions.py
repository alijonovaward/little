from rest_framework import permissions


class IsApprovedWholesaler(permissions.BasePermission):
    """
    Faqat is_wholesaler=True va is_approved=True bo'lgan foydalanuvchilarga ruxsat beradi.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            getattr(request.user, 'is_wholesaler', False) and
            getattr(request.user, 'is_approved', False)
        )