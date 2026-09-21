from decimal import Decimal

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from boxes.models import Box, Order, OrderItem, Product


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def sample_data(db):
    prod_small = Product.objects.create(
        sku="PROD-S",
        name="Small Item",
        length=Decimal("10.00"),
        width=Decimal("10.00"),
        height=Decimal("10.00"),
        weight=Decimal("0.500"),
        is_active=True,
    )
    prod_inactive = Product.objects.create(
        sku="PROD-INACTIVE",
        name="Inactive Item",
        length=Decimal("5.00"),
        width=Decimal("5.00"),
        height=Decimal("5.00"),
        weight=Decimal("0.100"),
        is_active=False,
    )
    box_med = Box.objects.create(
        name="Medium Box",
        internal_length=Decimal("30.00"),
        internal_width=Decimal("20.00"),
        internal_height=Decimal("15.00"),
        max_weight=Decimal("5.000"),
        cost=Decimal("1.80"),
        is_active=True,
    )
    box_large = Box.objects.create(
        name="Large Box",
        internal_length=Decimal("40.00"),
        internal_width=Decimal("30.00"),
        internal_height=Decimal("20.00"),
        max_weight=Decimal("10.000"),
        cost=Decimal("2.50"),
        is_active=True,
    )

    return {
        "prod_small": prod_small,
        "prod_inactive": prod_inactive,
        "box_med": box_med,
        "box_large": box_large,
    }


@pytest.mark.django_db
class TestProductAPI:
    def test_list_products(self, api_client, sample_data):
        res = api_client.get("/api/v1/products/")
        assert res.status_code == status.HTTP_200_OK
        assert res.data["count"] == 2

    def test_filter_active_products(self, api_client, sample_data):
        res = api_client.get("/api/v1/products/?is_active=true")
        assert res.status_code == status.HTTP_200_OK
        assert res.data["count"] == 1
        assert res.data["results"][0]["sku"] == "PROD-S"

    def test_create_product(self, api_client):
        payload = {
            "sku": "NEW-PROD",
            "name": "New Product",
            "length": "12.50",
            "width": "8.00",
            "height": "4.00",
            "weight": "0.300",
            "is_active": True,
        }
        res = api_client.post("/api/v1/products/", payload, format="json")
        assert res.status_code == status.HTTP_201_CREATED
        assert Product.objects.filter(sku="NEW-PROD").exists()


@pytest.mark.django_db
class TestBoxAPI:
    def test_list_boxes(self, api_client, sample_data):
        res = api_client.get("/api/v1/boxes/")
        assert res.status_code == status.HTTP_200_OK
        assert res.data["count"] == 2


@pytest.mark.django_db
class TestOrderAPI:
    def test_create_order_with_items(self, api_client, sample_data):
        payload = {
            "reference": "ORD-2001",
            "items": [{"sku": "PROD-S", "quantity": 2}],
        }
        res = api_client.post("/api/v1/orders/", payload, format="json")
        assert res.status_code == status.HTTP_201_CREATED
        assert Order.objects.filter(reference="ORD-2001").exists()

    def test_get_order_recommendation(self, api_client, sample_data):
        order = Order.objects.create(reference="ORD-2002")
        OrderItem.objects.create(order=order, product=sample_data["prod_small"], quantity=2)

        res = api_client.get(f"/api/v1/orders/{order.id}/recommend-box/")
        assert res.status_code == status.HTTP_200_OK
        assert res.data["status"] == "RECOMMENDED"
        assert res.data["recommended_box"]["name"] == "Medium Box"
        assert len(res.data["placements"]) == 2


@pytest.mark.django_db
class TestAdHocRecommendationAPI:
    def test_ad_hoc_recommendation_happy_path(self, api_client, sample_data):
        payload = {"items": [{"sku": "PROD-S", "quantity": 3}]}
        res = api_client.post("/api/v1/recommend-box/", payload, format="json")
        assert res.status_code == status.HTTP_200_OK
        assert res.data["status"] == "RECOMMENDED"
        assert res.data["recommended_box"]["name"] == "Medium Box"
        assert "placements" in res.data
        assert "order_summary" in res.data
        assert "utilisation" in res.data

    def test_merge_duplicate_skus(self, api_client, sample_data):
        payload = {
            "items": [
                {"sku": "PROD-S", "quantity": 2},
                {"sku": "PROD-S", "quantity": 1},
            ]
        }
        res = api_client.post("/api/v1/recommend-box/", payload, format="json")
        assert res.status_code == status.HTTP_200_OK
        assert res.data["order_summary"]["total_items"] == 3

    def test_inactive_product_in_request_returns_400(self, api_client, sample_data):
        payload = {"items": [{"sku": "PROD-INACTIVE", "quantity": 1}]}
        res = api_client.post("/api/v1/recommend-box/", payload, format="json")
        assert res.status_code == status.HTTP_400_BAD_REQUEST
        assert "error" in res.data
        assert "inactive" in str(res.data["error"]["message"])

    def test_unknown_sku_returns_400(self, api_client, sample_data):
        payload = {"items": [{"sku": "NON-EXISTENT", "quantity": 1}]}
        res = api_client.post("/api/v1/recommend-box/", payload, format="json")
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_empty_items_returns_400(self, api_client):
        payload = {"items": []}
        res = api_client.post("/api/v1/recommend-box/", payload, format="json")
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_negative_quantity_returns_400(self, api_client, sample_data):
        payload = {"items": [{"sku": "PROD-S", "quantity": -1}]}
        res = api_client.post("/api/v1/recommend-box/", payload, format="json")
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_filter_inactive_products(self, api_client, sample_data):
        res = api_client.get("/api/v1/products/?is_active=false")
        assert res.status_code == status.HTTP_200_OK
        assert res.data["count"] == 1
        assert res.data["results"][0]["sku"] == "PROD-INACTIVE"

    def test_filter_inactive_boxes(self, api_client, sample_data):
        res = api_client.get("/api/v1/boxes/?is_active=false")
        assert res.status_code == status.HTTP_200_OK
        assert res.data["count"] == 0

    def test_empty_order_recommendation_returns_400(self, api_client):
        order = Order.objects.create(reference="ORD-EMPTY")
        res = api_client.get(f"/api/v1/orders/{order.id}/recommend-box/")
        assert res.status_code == status.HTTP_400_BAD_REQUEST
        assert "contains no items" in str(res.data["error"]["message"])

    def test_exceeding_max_200_units_returns_400(self, api_client, sample_data):
        payload = {"items": [{"sku": "PROD-S", "quantity": 201}]}
        res = api_client.post("/api/v1/recommend-box/", payload, format="json")
        assert res.status_code == status.HTTP_400_BAD_REQUEST
        assert "exceeds the max limit of 200 units" in str(res.data["error"]["message"])

    def test_order_not_found_returns_404(self, api_client):
        res = api_client.get("/api/v1/orders/99999/recommend-box/")
        assert res.status_code == status.HTTP_404_NOT_FOUND
