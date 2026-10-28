"""Storage points — the places where travelers leave their bags."""

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class District(models.TextChoices):
    """The districts of Almaty, as a fixed list.

    The MVP has no map and no address search: a traveler picks a district and
    sees the cards of that district, so the list has to be closed and stable.
    """

    ALATAU = "alatau", "Alatau"
    ALMALY = "almaly", "Almaly"
    AUEZOV = "auezov", "Auezov"
    BOSTANDYK = "bostandyk", "Bostandyk"
    MEDEU = "medeu", "Medeu"
    NAURYZBAI = "nauryzbai", "Nauryzbai"
    TURKSIB = "turksib", "Turksib"
    ZHETYSU = "zhetysu", "Zhetysu"


class StoragePointQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True)

    def in_district(self, district):
        return self.filter(district=district)


class StoragePoint(models.Model):
    """One physical place with secure space for bags."""

    partner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="storage_points",
        limit_choices_to={"role": "partner"},
        verbose_name=_("partner"),
    )
    name = models.CharField(_("name"), max_length=120)
    address = models.CharField(_("address"), max_length=255)
    district = models.CharField(
        _("district"),
        max_length=32,
        choices=District.choices,
        db_index=True,
    )

    price_per_bag_per_hour = models.DecimalField(
        _("price per bag per hour"),
        max_digits=8,
        decimal_places=2,
        help_text=_("In KZT. The total is price × bags × hours."),
    )
    capacity_bags = models.PositiveSmallIntegerField(
        _("capacity in bags"),
        help_text=_("How many bags fit in total."),
    )

    opens_at = models.TimeField(_("opens at"))
    closes_at = models.TimeField(_("closes at"))
    security_notes = models.TextField(_("security notes"), blank=True)

    is_active = models.BooleanField(
        _("active"),
        default=True,
        help_text=_("A partner hides a point instead of deleting it."),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = StoragePointQuerySet.as_manager()

    class Meta:
        db_table = "storage_points"
        verbose_name = _("storage point")
        verbose_name_plural = _("storage points")
        ordering = ("name",)
        indexes = [
            models.Index(fields=["district", "is_active"], name="sp_district_active_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(capacity_bags__gt=0),
                name="sp_capacity_positive",
            ),
            models.CheckConstraint(
                condition=models.Q(price_per_bag_per_hour__gte=0),
                name="sp_price_non_negative",
            ),
            # `choices` is only checked by forms and serializers, so the allowed
            # districts are repeated here for the database itself.
            models.CheckConstraint(
                condition=models.Q(district__in=District.values),
                name="sp_district_valid",
            ),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_district_display()})"
