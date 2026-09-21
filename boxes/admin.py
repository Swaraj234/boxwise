from django.contrib import admin

from .models import Box, BoxRecommendation, Order, OrderItem, Product


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1
    raw_id_fields = ("product",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "sku",
        "name",
        "length",
        "width",
        "height",
        "weight",
        "is_active",
        "created_at",
    )
    list_filter = ("is_active", "created_at")
    search_fields = ("sku", "name")
    ordering = ("sku",)


@admin.register(Box)
class BoxAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "internal_length",
        "internal_width",
        "internal_height",
        "max_weight",
        "cost",
        "is_active",
        "created_at",
    )
    list_filter = ("is_active", "created_at")
    search_fields = ("name",)
    ordering = ("cost", "name")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "reference", "created_at", "get_item_count")
    search_fields = ("reference",)
    inlines = [OrderItemInline]

    @admin.display(description="Item Count")
    def get_item_count(self, obj) -> int:
        return obj.items.count()


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "product", "quantity")
    list_filter = ("order", "product")
    search_fields = ("order__reference", "product__sku", "product__name")


@admin.register(BoxRecommendation)
class BoxRecommendationAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "recommended_box", "result_status", "created_at")
    list_filter = ("result_status", "created_at")
    search_fields = ("order__reference", "recommended_box__name")
    readonly_fields = ("order", "recommended_box", "result_status", "payload", "created_at")
