from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AdHocRecommendBoxView,
    BoxViewSet,
    OrderViewSet,
    ProductViewSet,
)

router = DefaultRouter()
router.register(r"products", ProductViewSet, basename="product")
router.register(r"boxes", BoxViewSet, basename="box")
router.register(r"orders", OrderViewSet, basename="order")

urlpatterns = [
    path("recommend-box/", AdHocRecommendBoxView.as_view(), name="recommend-box"),
    path("", include(router.urls)),
]
