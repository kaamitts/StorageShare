from django.contrib import admin

from storage.models import StoragePoint


@admin.register(StoragePoint)
class StoragePointAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "district",
        "partner",
        "price_per_bag_per_hour",
        "capacity_bags",
        "is_active",
    )
    list_filter = ("district", "is_active")
    search_fields = ("name", "address", "partner__email", "partner__full_name")
    list_select_related = ("partner",)
    ordering = ("district", "name")
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        (None, {"fields": ("partner", "name", "is_active")}),
        ("Location", {"fields": ("district", "address")}),
        ("Price and capacity", {"fields": ("price_per_bag_per_hour", "capacity_bags")}),
        ("Opening hours", {"fields": ("opens_at", "closes_at")}),
        ("Extra", {"fields": ("security_notes", "created_at", "updated_at")}),
    )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Only partner accounts can own a storage point.
        if db_field.name == "partner":
            from django.contrib.auth import get_user_model

            kwargs["queryset"] = get_user_model().objects.filter(role="partner")
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
