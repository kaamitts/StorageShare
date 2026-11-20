"""Serializers for registration, login and the current-user endpoint."""

from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed, NotFound
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import UserRole

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """The user object returned to the frontend. Never contains the password."""

    class Meta:
        model = User
        fields = ("id", "email", "full_name", "phone", "role", "created_at", "is_admin")
        read_only_fields = fields

    is_admin = serializers.BooleanField(source="is_superuser", read_only=True)


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """Allow users to edit contact details, while keeping identity and role fixed."""

    full_name = serializers.CharField(max_length=120, allow_blank=False, trim_whitespace=True)
    phone = serializers.RegexField(
        regex=r"^\+[1-9]\d{6,14}$",
        max_length=16,
        allow_blank=True,
        required=False,
        error_messages={"invalid": "Enter a phone number with country code and 7–15 digits."},
    )

    class Meta:
        model = User
        fields = ("id", "email", "full_name", "phone", "role", "created_at")
        read_only_fields = ("id", "email", "role", "created_at")

    def validate(self, attrs):
        allowed = {"full_name", "phone"}
        unexpected = set(self.initial_data) - allowed
        if unexpected:
            raise serializers.ValidationError(
                {field: "This field cannot be changed here." for field in sorted(unexpected)}
            )
        return attrs


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={"input_type": "password"},
    )
    role = serializers.ChoiceField(choices=UserRole.choices, required=True)
    full_name = serializers.CharField(max_length=120, required=True, allow_blank=False)

    class Meta:
        model = User
        fields = ("email", "password", "full_name", "phone", "role")

    def validate_email(self, value):
        # Compare case-insensitively: Aizhan@x.com and aizhan@x.com are one person.
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value.lower()

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class LoginSerializer(TokenObtainPairSerializer):
    """Email + password login.

    Overridden for two reasons: to return one clear error instead of the
    library default, and to put the role inside the access token so the
    frontend can route to the traveler app or the partner dashboard.
    """

    username_field = User.USERNAME_FIELD

    default_error_messages = {
        "no_active_account": "Invalid email or password.",
    }

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = user.role
        token["email"] = user.email
        token["is_admin"] = user.is_superuser
        return token

    def validate(self, attrs):
        email = attrs.get(self.username_field, "")
        attrs[self.username_field] = email.lower()

        if not User.objects.filter(email__iexact=email).exists():
            raise NotFound("No account with this email exists.")

        user = authenticate(
            request=self.context.get("request"),
            username=attrs[self.username_field],
            password=attrs["password"],
        )
        # Keep a generic message for existing accounts with a wrong password
        # or a disabled account.
        if user is None:
            raise AuthenticationFailed("Invalid email or password.")

        refresh = self.get_token(user)
        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": UserSerializer(user).data,
        }


class SafeTokenRefreshSerializer(TokenRefreshSerializer):
    """Treat refresh tokens for deleted accounts as invalid instead of a server error."""

    def validate(self, attrs):
        try:
            return super().validate(attrs)
        except User.DoesNotExist as error:
            raise InvalidToken(
                "This refresh token belongs to an account that no longer exists."
            ) from error


class LogoutSerializer(serializers.Serializer):
    """Blacklists the refresh token so it cannot be used again."""

    refresh = serializers.CharField()

    def save(self, **kwargs):
        try:
            RefreshToken(self.validated_data["refresh"]).blacklist()
        except Exception:
            raise serializers.ValidationError({"refresh": "Invalid or expired token."})
