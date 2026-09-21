from django.conf import settings
from django.db import transaction
from rest_framework import serializers

from .models import Box, BoxRecommendation, Order, OrderItem, Product


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            "id",
            "sku",
            "name",
            "length",
            "width",
            "height",
            "weight",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class BoxSerializer(serializers.ModelSerializer):
    class Meta:
        model = Box
        fields = [
            "id",
            "name",
            "internal_length",
            "internal_width",
            "internal_height",
            "max_weight",
            "empty_weight",
            "cost",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class OrderItemCreateSerializer(serializers.ModelSerializer):
    sku = serializers.CharField(write_only=True)

    class Meta:
        model = OrderItem
        fields = ["sku", "quantity"]

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be a positive integer.")
        return value


class OrderItemDetailSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = ["id", "product", "quantity"]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemCreateSerializer(many=True, write_only=True, required=True)
    order_items = OrderItemDetailSerializer(source="items", many=True, read_only=True)

    class Meta:
        model = Order
        fields = ["id", "reference", "created_at", "items", "order_items"]
        read_only_fields = ["id", "created_at", "order_items"]

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("Order must contain at least one item.")

        total_qty = sum(item["quantity"] for item in value)
        max_limit = getattr(settings, "MAX_ORDER_ITEMS", 200)
        if total_qty > max_limit:
            raise serializers.ValidationError(
                f"Total order item quantity ({total_qty}) exceeds limit of {max_limit} units."
            )

        # Merge duplicate SKUs
        sku_qty_map: dict[str, int] = {}
        for item in value:
            sku = item["sku"]
            sku_qty_map[sku] = sku_qty_map.get(sku, 0) + item["quantity"]

        # Validate products exist and are active
        for sku in sku_qty_map:
            try:
                prod = Product.objects.get(sku=sku)
                if not prod.is_active:
                    raise serializers.ValidationError(f"Product with SKU '{sku}' is inactive.")
            except Product.DoesNotExist as err:
                raise serializers.ValidationError(
                    f"Product with SKU '{sku}' does not exist."
                ) from err

        return [{"sku": k, "quantity": v} for k, v in sku_qty_map.items()]

    def create(self, validated_data):
        items_data = validated_data.pop("items")
        with transaction.atomic():
            order = Order.objects.create(**validated_data)
            for item_info in items_data:
                product = Product.objects.get(sku=item_info["sku"])
                OrderItem.objects.create(
                    order=order, product=product, quantity=item_info["quantity"]
                )
        return order


class AdHocItemRequestSerializer(serializers.Serializer):
    sku = serializers.CharField(max_length=100)
    quantity = serializers.IntegerField(min_value=1)


class AdHocRecommendBoxRequestSerializer(serializers.Serializer):
    items = AdHocItemRequestSerializer(many=True, allow_empty=False)

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("Items list cannot be empty.")

        total_qty = sum(item["quantity"] for item in value)
        max_limit = getattr(settings, "MAX_ORDER_ITEMS", 200)
        if total_qty > max_limit:
            raise serializers.ValidationError(
                f"Total item quantity ({total_qty}) exceeds the max limit of {max_limit} units."
            )

        # Merge duplicate SKUs
        merged_skus: dict[str, int] = {}
        for item in value:
            sku = item["sku"]
            merged_skus[sku] = merged_skus.get(sku, 0) + item["quantity"]

        # Validate existence and activity
        for sku in merged_skus:
            try:
                prod = Product.objects.get(sku=sku)
                if not prod.is_active:
                    raise serializers.ValidationError(f"Product with SKU '{sku}' is inactive.")
            except Product.DoesNotExist as err:
                raise serializers.ValidationError(
                    f"Product with SKU '{sku}' does not exist."
                ) from err

        return [{"sku": k, "quantity": v} for k, v in merged_skus.items()]


class BoxRecommendationSerializer(serializers.ModelSerializer):
    class Meta:
        model = BoxRecommendation
        fields = ["id", "order", "recommended_box", "result_status", "payload", "created_at"]
        read_only_fields = fields
