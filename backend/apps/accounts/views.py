import hashlib
import logging
import secrets
from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.core.email import send_transactional_email

from .models import (
    Address,
    AuditLog,
    EmailVerificationToken,
    PasswordResetToken,
    User,
)
from .serializers import (
    AddressSerializer,
    LoginSerializer,
    PasswordChangeSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    ProfileSerializer,
    RegisterSerializer,
    UserSerializer,
    VerifyEmailSerializer,
)
from .throttles import LoginRateThrottle, ResetRateThrottle

logger = logging.getLogger(__name__)

# Cookie name used for the httpOnly refresh token
REFRESH_COOKIE_NAME = "refresh_token"
REFRESH_COOKIE_MAX_AGE = int(timedelta(days=30).total_seconds())


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    response.set_cookie(
        REFRESH_COOKIE_NAME,
        refresh_token,
        max_age=REFRESH_COOKIE_MAX_AGE,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="Lax",
        path="/api/v1/auth/",
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(REFRESH_COOKIE_NAME, path="/api/v1/auth/")


def _get_tokens_for_user(user: User) -> dict:
    refresh = RefreshToken.for_user(user)
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    }


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


class RegisterView(APIView):
    """
    POST /api/v1/auth/register/
    Create a new user account. When REQUIRE_EMAIL_VERIFICATION is True, sends a verification email.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        if settings.REQUIRE_EMAIL_VERIFICATION:
            token = EmailVerificationToken.objects.create(
                user=user,
                expires_at=timezone.now() + timedelta(hours=24),
            )
            verification_url = f"{settings.FRONTEND_URL if hasattr(settings, 'FRONTEND_URL') else 'http://localhost:3000'}/verify-email/{token.id}"
            try:
                send_transactional_email(
                    subject="Verify your Upstream Literacy account",
                    message=(
                        f"Hi {user.first_name},\n\n"
                        f"Please verify your email address by clicking the link below:\n\n"
                        f"{verification_url}\n\n"
                        "This link expires in 24 hours.\n\n"
                        "If you did not create an account, please ignore this email."
                    ),
                    to_emails=[user.email],
                )
            except Exception:
                logger.exception("Failed to send verification email to %s", user.email)
            message = "Account created. Please check your email to verify your account."
        else:
            user.is_verified = True
            user.save(update_fields=["is_verified"])
            message = "Account created."

        return Response(
            {"message": message, "user": UserSerializer(user).data},
            status=status.HTTP_201_CREATED,
        )


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------


class LoginView(APIView):
    """
    POST /api/v1/auth/login/
    Authenticate user, return JWT access token in body and refresh token as httpOnly cookie.
    """

    permission_classes = [AllowAny]
    throttle_classes = [LoginRateThrottle]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        tokens = _get_tokens_for_user(user)
        response = Response(
            {
                "access": tokens["access"],
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_200_OK,
        )
        _set_refresh_cookie(response, tokens["refresh"])
        return response


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------


class LogoutView(APIView):
    """
    POST /api/v1/auth/logout/
    Blacklist the refresh token and clear the cookie.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Try to get the refresh token from body or cookie
        refresh_token_str = request.data.get("refresh") or request.COOKIES.get(REFRESH_COOKIE_NAME)

        if refresh_token_str:
            try:
                token = RefreshToken(refresh_token_str)
                token.blacklist()
            except TokenError:
                pass  # Already blacklisted or invalid — still clear the cookie

        response = Response({"message": "Logged out successfully."}, status=status.HTTP_200_OK)
        _clear_refresh_cookie(response)
        return response


# ---------------------------------------------------------------------------
# Token Refresh (cookie-aware)
# ---------------------------------------------------------------------------


class CookieTokenRefreshView(APIView):
    """
    POST /api/v1/auth/token/refresh/
    Reads the refresh token from the httpOnly cookie if not present in the request body.
    Returns a new access token (and rotated refresh token).
    """

    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token_str = request.data.get("refresh") or request.COOKIES.get(REFRESH_COOKIE_NAME)

        if not refresh_token_str:
            return Response(
                {"error": {"code": "missing_token", "message": "Refresh token not provided.", "field_errors": {}}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            old_token = RefreshToken(refresh_token_str)
            # With ROTATE_REFRESH_TOKENS=True this creates a new refresh token
            access_token = old_token.access_token
            # Force rotation
            new_refresh = RefreshToken.for_user(
                User.objects.get(id=old_token["user_id"])
            )
            # Blacklist the old token
            old_token.blacklist()
        except TokenError as exc:
            return Response(
                {"error": {"code": "token_invalid", "message": str(exc), "field_errors": {}}},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        except User.DoesNotExist:
            return Response(
                {"error": {"code": "user_not_found", "message": "User not found.", "field_errors": {}}},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        response = Response({"access": str(new_refresh.access_token)}, status=status.HTTP_200_OK)
        _set_refresh_cookie(response, str(new_refresh))
        return response


# ---------------------------------------------------------------------------
# Email Verification
# ---------------------------------------------------------------------------


class VerifyEmailView(APIView):
    """
    POST /api/v1/auth/verify-email/
    Mark the user's email as verified using the provided token UUID.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token_id = serializer.validated_data["token"]

        try:
            token = EmailVerificationToken.objects.select_related("user").get(id=token_id)
        except EmailVerificationToken.DoesNotExist:
            return Response(
                {"error": {"code": "invalid_token", "message": "Invalid verification token.", "field_errors": {}}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not token.is_valid():
            return Response(
                {"error": {"code": "token_expired", "message": "This verification link has expired. Please request a new one.", "field_errors": {}}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = token.user
        if not user.is_verified:
            user.is_verified = True
            user.save(update_fields=["is_verified"])

        token.delete()

        return Response({"message": "Email verified successfully. You may now sign in."}, status=status.HTTP_200_OK)


# ---------------------------------------------------------------------------
# Resend Verification
# ---------------------------------------------------------------------------


class ResendVerificationView(APIView):
    """
    POST /api/v1/auth/verify-email/resend/
    Send a new verification email to the given address.
    """

    permission_classes = [AllowAny]
    throttle_classes = [ResetRateThrottle]

    def post(self, request):
        email = request.data.get("email", "").lower().strip()

        if not settings.REQUIRE_EMAIL_VERIFICATION:
            return Response(
                {"message": "If an account with that email exists, a new verification link has been sent."},
                status=status.HTTP_200_OK,
            )

        # Always return 200 to prevent user enumeration
        if not email:
            return Response(
                {"message": "If an account with that email exists, a new verification link has been sent."},
                status=status.HTTP_200_OK,
            )

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"message": "If an account with that email exists, a new verification link has been sent."},
                status=status.HTTP_200_OK,
            )

        if user.is_verified:
            return Response(
                {"message": "This email address has already been verified."},
                status=status.HTTP_200_OK,
            )

        # Delete old token and create a new one
        EmailVerificationToken.objects.filter(user=user).delete()
        token = EmailVerificationToken.objects.create(
            user=user,
            expires_at=timezone.now() + timedelta(hours=24),
        )

        frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:3000")
        verification_url = f"{frontend_url}/verify-email/{token.id}"

        try:
            send_transactional_email(
                subject="Verify your Upstream Literacy account",
                message=(
                    f"Hi {user.first_name},\n\n"
                    f"Here is your new verification link:\n\n"
                    f"{verification_url}\n\n"
                    "This link expires in 24 hours."
                ),
                to_emails=[user.email],
            )
        except Exception:
            logger.exception("Failed to resend verification email to %s", email)

        return Response(
            {"message": "If an account with that email exists, a new verification link has been sent."},
            status=status.HTTP_200_OK,
        )


# ---------------------------------------------------------------------------
# Password Reset Request
# ---------------------------------------------------------------------------


class PasswordResetRequestView(APIView):
    """
    POST /api/v1/auth/password/reset/
    Send a password reset email. Always returns 200 to prevent enumeration.
    """

    permission_classes = [AllowAny]
    throttle_classes = [ResetRateThrottle]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"].lower()

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"message": "If an account with that email exists, a password reset link has been sent."},
                status=status.HTTP_200_OK,
            )

        # Generate a cryptographically secure token
        raw_token = secrets.token_hex(32)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

        PasswordResetToken.objects.create(
            user=user,
            token_hash=token_hash,
            expires_at=timezone.now() + timedelta(hours=2),
        )

        frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:3000")
        reset_url = f"{frontend_url}/reset-password?token={raw_token}&uid={user.id}"

        try:
            send_transactional_email(
                subject="Reset your Upstream Literacy password",
                message=(
                    f"Hi {user.first_name},\n\n"
                    f"Click the link below to reset your password:\n\n"
                    f"{reset_url}\n\n"
                    "This link expires in 2 hours. If you did not request a password reset, "
                    "please ignore this email."
                ),
                to_emails=[user.email],
            )
        except Exception:
            logger.exception("Failed to send password reset email to %s", email)

        return Response(
            {"message": "If an account with that email exists, a password reset link has been sent."},
            status=status.HTTP_200_OK,
        )


# ---------------------------------------------------------------------------
# Password Reset Confirm
# ---------------------------------------------------------------------------


class PasswordResetConfirmView(APIView):
    """
    POST /api/v1/auth/password/reset/confirm/
    Validate the reset token and set the new password.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        raw_token = str(serializer.validated_data["token"])
        new_password = serializer.validated_data["new_password"]

        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

        try:
            reset_token = PasswordResetToken.objects.select_related("user").get(
                token_hash=token_hash,
                used=False,
            )
        except PasswordResetToken.DoesNotExist:
            return Response(
                {"error": {"code": "invalid_token", "message": "Invalid or expired reset token.", "field_errors": {}}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not reset_token.is_valid():
            return Response(
                {"error": {"code": "token_expired", "message": "This reset link has expired. Please request a new one.", "field_errors": {}}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = reset_token.user
        user.set_password(new_password)
        user.save(update_fields=["password"])

        # Mark this token as used and invalidate all other reset tokens for the user
        reset_token.used = True
        reset_token.save(update_fields=["used"])
        PasswordResetToken.objects.filter(user=user, used=False).update(used=True)

        # Blacklist all outstanding refresh tokens (via simplejwt token_blacklist)
        # This logs the user out of all devices
        try:
            from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
            outstanding = OutstandingToken.objects.filter(user=user)
            for token in outstanding:
                BlacklistedToken.objects.get_or_create(token=token)
        except Exception:
            logger.exception("Failed to blacklist outstanding tokens for user %s", user.id)

        return Response({"message": "Password reset successful. You may now sign in with your new password."}, status=status.HTTP_200_OK)


# ---------------------------------------------------------------------------
# Password Change (authenticated)
# ---------------------------------------------------------------------------


class PasswordChangeView(APIView):
    """
    POST /api/v1/auth/password/change/
    Change password for the currently authenticated user.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        user = request.user
        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password"])

        return Response({"message": "Password changed successfully."}, status=status.HTTP_200_OK)


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------


class ProfileView(generics.RetrieveUpdateAPIView):
    """
    GET  /api/v1/accounts/profile/  — Return current user's profile.
    PATCH /api/v1/accounts/profile/ — Update current user's profile.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = ProfileSerializer

    def get_object(self):
        return self.request.user


# ---------------------------------------------------------------------------
# Addresses
# ---------------------------------------------------------------------------


class AddressViewSet(viewsets.ModelViewSet):
    """
    CRUD for the authenticated user's addresses.
    Extra action: POST addresses/{id}/set_default/
    """

    permission_classes = [IsAuthenticated]
    serializer_class = AddressSerializer

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"], url_path="set-default")
    def set_default(self, request, pk=None):
        address = self.get_object()
        address.is_default = True
        address.save()  # Address.save() clears other defaults automatically
        return Response(AddressSerializer(address).data, status=status.HTTP_200_OK)


# ---------------------------------------------------------------------------
# Claim Guest Account
# ---------------------------------------------------------------------------


class ClaimGuestView(APIView):
    """
    POST /api/v1/accounts/claim-guest/
    Convert a guest account into a full account after the user registers.
    Requires the authenticated user to provide the guest's email.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        guest_email = request.data.get("guest_email", "").lower().strip()
        if not guest_email:
            return Response(
                {"error": {"code": "missing_field", "message": "guest_email is required.", "field_errors": {}}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            guest = User.objects.get(email=guest_email, is_guest=True)
        except User.DoesNotExist:
            return Response(
                {"error": {"code": "not_found", "message": "No guest account found with that email.", "field_errors": {}}},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Merge: transfer any guest orders to the real user
        # (actual transfer logic lives in the orders app)
        from django.apps import apps

        Order = apps.get_model("orders", "Order") if apps.is_installed("apps.orders") else None
        if Order is not None:
            Order.objects.filter(user=guest).update(user=request.user)

        guest.delete()

        return Response({"message": "Guest account merged successfully."}, status=status.HTTP_200_OK)
