from decimal import Decimal

import pytest
from django.db.utils import IntegrityError

from boxes.models import Box, BoxRecommendation, Order, OrderItem, Product


@pytest.mark.django_db
class TestProductModel:
    def test_create_valid_product(self):
        product = Product.objects.create(
            sku="PROD-001",
            name="Test Widget",
            length=Decimal("10.50"),
            width=Decimal("5.00"),
            height=Decimal("2.25"),
            weight=Decimal("0.750"),
            is_active=True,
        )
        assert product.id is not None
        assert str(product) == "Test Widget (PROD-001)"
        assert product.volume == Decimal("10.50") * Decimal("5.00") * Decimal("2.25")

    def test_product_dimension_check_constraint(self):
        with pytest.raises(IntegrityError):
            Product.objects.create(
                sku="PROD-BAD",
                name="Bad Widget",
                length=Decimal("0.00"),
                width=Decimal("5.00"),
                height=Decimal("2.00"),
                weight=Decimal("1.000"),
            )

    def test_product_weight_check_constraint(self):
        with pytest.raises(IntegrityError):
            Product.objects.create(
                sku="PROD-BAD-WT",
                name="Bad Weight",
                length=Decimal("10.00"),
                width=Decimal("5.00"),
                height=Decimal("2.00"),
                weight=Decimal("0.000"),
            )


@pytest.mark.django_db
class TestBoxModel:
    def test_create_valid_box(self):
        box = Box.objects.create(
            name="Medium Box",
            internal_length=Decimal("30.00"),
            internal_width=Decimal("20.00"),
            internal_height=Decimal("15.00"),
            max_weight=Decimal("5.000"),
            empty_weight=Decimal("0.200"),
            cost=Decimal("1.50"),
            is_active=True,
        )
        assert box.id is not None
        assert str(box) == "Medium Box (30.00x20.00x15.00 cm, $1.50)"
        assert box.volume == Decimal("30.00") * Decimal("20.00") * Decimal("15.00")

    def test_box_check_constraints(self):
        with pytest.raises(IntegrityError):
            Box.objects.create(
                name="Invalid Box",
                internal_length=Decimal("-1.00"),
                internal_width=Decimal("10.00"),
                internal_height=Decimal("10.00"),
                max_weight=Decimal("5.000"),
                cost=Decimal("1.00"),
            )


@pytest.mark.django_db
class TestOrderAndItems:
    def test_create_order_with_items(self):
        product = Product.objects.create(
            sku="SKU-A",
            name="Item A",
            length=Decimal("10.00"),
            width=Decimal("10.00"),
            height=Decimal("10.00"),
            weight=Decimal("1.000"),
        )
        order = Order.objects.create(reference="ORD-1001")
        item = OrderItem.objects.create(order=order, product=product, quantity=3)

        assert item.id is not None
        assert order.items.count() == 1
        assert str(item) == "3x SKU-A (Order ORD-1001)"

    def test_order_item_unique_together(self):
        product = Product.objects.create(
            sku="SKU-UNIQUE",
            name="Item Unique",
            length=Decimal("10.00"),
            width=Decimal("10.00"),
            height=Decimal("10.00"),
            weight=Decimal("1.000"),
        )
        order = Order.objects.create(reference="ORD-1002")
        OrderItem.objects.create(order=order, product=product, quantity=1)

        with pytest.raises(IntegrityError):
            OrderItem.objects.create(order=order, product=product, quantity=2)


@pytest.mark.django_db
class TestBoxRecommendationModel:
    def test_create_box_recommendation(self):
        order = Order.objects.create(reference="ORD-REC-1")
        box = Box.objects.create(
            name="Rec Box",
            internal_length=Decimal("20.00"),
            internal_width=Decimal("20.00"),
            internal_height=Decimal("20.00"),
            max_weight=Decimal("5.000"),
            cost=Decimal("2.00"),
        )
        rec = BoxRecommendation.objects.create(
            order=order,
            recommended_box=box,
            result_status="RECOMMENDED",
            payload={"test": "data"},
        )
        assert rec.id is not None
        assert rec.recommended_box == box
        assert "RECOMMENDED" in str(rec)
