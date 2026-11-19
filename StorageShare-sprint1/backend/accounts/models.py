"""Users of both sides of the marketplace: travelers and partners."""

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _


class UserRole(models.TextChoices):
    """Which side of the marketplace the account belongs to.

    Declared at module level so that `User.Meta` below can reach it.
    """

    TRAVELER = "traveler", "Traveler"
    PARTNER = "partner", "Partner"


class UserManager(BaseUserManager):
    """Manager for a user model that logs in by email instead of username."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", UserRole.PARTNER)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True")
        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """One user table for travelers and partners, separated by `role`.

    A single table is enough: login, password and tokens work identically for
    both sides of the marketplace, and only the permissions differ.
    """

    # Exposed as User.Role for convenience.
    Role = UserRole

    # Login is by email, so the inherited username fields are removed.
    username = None
    first_name = None
    last_name = None

    email = models.EmailField(
        _("email address"),
        unique=True,
        error_messages={"unique": _("A user with this email already exists.")},
    )
    full_name = models.CharField(_("full name"), max_length=120, blank=True)
    phone = models.CharField(_("phone"), max_length=32, blank=True)
    role = models.CharField(
        _("role"),
        max_length=16,
        choices=UserRole.choices,
        default=UserRole.TRAVELER,
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        db_table = "users"
        verbose_name = _("user")
        verbose_name_plural = _("users")
        constraints = [
            # `choices` is only enforced by forms and serializers, so the
            # allowed values are repeated here for the database itself.
            models.CheckConstraint(
                condition=models.Q(role__in=UserRole.values),
                name="users_role_valid",
            ),
        ]

    def __str__(self):
        return f"{self.email} ({self.role})"

    @property
    def is_traveler(self):
        return self.role == UserRole.TRAVELER

    @property
    def is_partner(self):
        return self.role == UserRole.PARTNER
