from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsVerifiedUser(BasePermission):
    """
    Allows access only to authenticated users whose email has been verified.
    """

    message = "Email verification is required to access this resource."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_verified
        )


class IsOwnerOrAdmin(BasePermission):
    """
    Object-level permission: allows access if the requesting user is the
    owner of the object (obj.user == request.user) or a staff member.
    """

    message = "You do not have permission to access this resource."

    def has_object_permission(self, request, view, obj):
        if request.user and request.user.is_staff:
            return True
        owner = getattr(obj, "user", None)
        return owner == request.user


class IsAdminUser(BasePermission):
    """Allow access only to admin/staff users."""

    message = "Admin access is required."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)


class IsOwnerOrReadOnly(BasePermission):
    """
    Object-level permission: read-only for any authenticated user,
    write access only to the owner or staff.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        if request.user and request.user.is_staff:
            return True
        owner = getattr(obj, "user", None)
        return owner == request.user
