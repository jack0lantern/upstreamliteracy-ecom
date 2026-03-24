from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from .models import Address, Institution, User, UserProfile


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8, style={"input_type": "password"})
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    role = serializers.ChoiceField(choices=User.Role.choices, default=User.Role.OTHER)

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email address already exists.")
        return value.lower()

    def validate_password(self, value):
        # Run all configured AUTH_PASSWORD_VALIDATORS
        validate_password(value)
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data["email"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
            password=validated_data["password"],
            role=validated_data.get("role", User.Role.OTHER),
        )
        UserProfile.objects.create(user=user)
        Institution.objects.create(user=user)
        return user


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate(self, attrs):
        email = attrs.get("email", "").lower()
        password = attrs.get("password", "")

        user = authenticate(request=self.context.get("request"), username=email, password=password)
        if not user:
            raise serializers.ValidationError(
                {"non_field_errors": [_("Invalid email or password.")]},
                code="authorization",
            )
        if not user.is_active:
            raise serializers.ValidationError(
                {"non_field_errors": [_("This account has been deactivated.")]},
                code="authorization",
            )
        if settings.REQUIRE_EMAIL_VERIFICATION and not user.is_verified:
            raise serializers.ValidationError(
                {"non_field_errors": [_("Please verify your email address before signing in.")]},
                code="email_not_verified",
            )
        attrs["user"] = user
        return attrs


# ---------------------------------------------------------------------------
# User (read)
# ---------------------------------------------------------------------------


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "role",
            "is_verified",
            "is_guest",
            "date_joined",
        ]
        read_only_fields = fields

    def get_full_name(self, obj):
        return obj.get_full_name()


# ---------------------------------------------------------------------------
# Profile (read / update)
# ---------------------------------------------------------------------------


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ["phone", "preferences"]


class InstitutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Institution
        fields = ["school_name", "district_name", "tax_exempt", "exemption_verified"]
        read_only_fields = ["tax_exempt", "exemption_verified"]


class ProfileSerializer(serializers.ModelSerializer):
    """
    Combined serializer for User + UserProfile + Institution.
    Supports nested read and update.
    """

    profile = UserProfileSerializer()
    institution = InstitutionSerializer()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "role",
            "is_verified",
            "date_joined",
            "profile",
            "institution",
        ]
        read_only_fields = ["id", "email", "is_verified", "date_joined"]

    def update(self, instance, validated_data):
        profile_data = validated_data.pop("profile", {})
        institution_data = validated_data.pop("institution", {})

        # Update User fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update UserProfile
        if profile_data:
            profile = instance.profile
            for attr, value in profile_data.items():
                setattr(profile, attr, value)
            profile.save()

        # Update Institution
        if institution_data:
            institution = instance.institution
            for attr, value in institution_data.items():
                setattr(institution, attr, value)
            institution.save()

        return instance


# ---------------------------------------------------------------------------
# Address
# ---------------------------------------------------------------------------


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = [
            "id",
            "label",
            "recipient_name",
            "line_1",
            "line_2",
            "city",
            "state",
            "zip",
            "country",
            "is_default",
        ]
        read_only_fields = ["id"]

    def validate_state(self, value):
        if len(value) != 2:
            raise serializers.ValidationError("State must be a 2-letter abbreviation.")
        return value.upper()

    def validate_country(self, value):
        if len(value) != 2:
            raise serializers.ValidationError("Country must be a 2-letter ISO code.")
        return value.upper()


# ---------------------------------------------------------------------------
# Password Reset
# ---------------------------------------------------------------------------


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.UUIDField()
    new_password = serializers.CharField(write_only=True, min_length=8, style={"input_type": "password"})

    def validate_new_password(self, value):
        validate_password(value)
        return value


class PasswordChangeSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True, style={"input_type": "password"})
    new_password = serializers.CharField(write_only=True, min_length=8, style={"input_type": "password"})

    def validate_current_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value

    def validate_new_password(self, value):
        validate_password(value, user=self.context["request"].user)
        return value


# ---------------------------------------------------------------------------
# Email Verification
# ---------------------------------------------------------------------------


class VerifyEmailSerializer(serializers.Serializer):
    token = serializers.UUIDField()
