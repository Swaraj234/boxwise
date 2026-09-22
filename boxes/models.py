from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q


class Product(models.Model):
    sku = models.CharField(max_length=100, unique=True, db_index=True)
    name = models.CharField(max_length=255)
    length = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text="Length in centimeters",
    )
    width = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text="Width in centimeters",
    )
    height = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text="Height in centimeters",
    )
    weight = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        validators=[MinValueValidator(Decimal("0.001"))],
        help_text="Weight in kilograms",
    )
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sku"]
        constraints = [
            models.CheckConstraint(condition=Q(length__gt=0), name="product_length_gt_zero"),
            models.CheckConstraint(condition=Q(width__gt=0), name="product_width_gt_zero"),
            models.CheckConstraint(condition=Q(height__gt=0), name="product_height_gt_zero"),
            models.CheckConstraint(condition=Q(weight__gt=0), name="product_weight_gt_zero"),
        ]

    @property
    def volume(self) -> Decimal:
        return self.length * self.width * self.height

    def __str__(self) -> str:
        return f"{self.name} ({self.sku})"


class Box(models.Model):
    name = models.CharField(max_length=100, unique=True)
    internal_length = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text="Internal length in centimeters",
    )
    internal_width = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text="Internal width in centimeters",
    )
    internal_height = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text="Internal height in centimeters",
    )
    max_weight = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        validators=[MinValueValidator(Decimal("0.001"))],
        help_text="Maximum contents weight limit in kilograms",
    )
    empty_weight = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        null=True,
        blank=True,
        default=Decimal("0.000"),
        help_text="Empty box tare weight in kilograms (ignored for limit by default)",
    )
    cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Box unit cost",
    )
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["cost", "name"]
        verbose_name_plural = "Boxes"
        constraints = [
            models.CheckConstraint(
                condition=Q(internal_length__gt=0), name="box_internal_length_gt_zero"
            ),
            models.CheckConstraint(
                condition=Q(internal_width__gt=0), name="box_internal_width_gt_zero"
            ),
            models.CheckConstraint(
                condition=Q(internal_height__gt=0), name="box_internal_height_gt_zero"
            ),
            models.CheckConstraint(condition=Q(max_weight__gt=0), name="box_max_weight_gt_zero"),
            models.CheckConstraint(condition=Q(cost__gte=0), name="box_cost_gte_zero"),
        ]

    @property
    def volume(self) -> Decimal:
        return self.internal_length * self.internal_width * self.internal_height

    def __str__(self) -> str:
        return (
            f"{self.name} ({self.internal_length}x{self.internal_width}x"
            f"{self.internal_height} cm, ${self.cost})"
        )


class Order(models.Model):
    reference = models.CharField(max_length=100, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Order {self.reference}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="order_items")
    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)], help_text="Number of units"
    )

    class Meta:
        unique_together = ("order", "product")
        constraints = [
            models.CheckConstraint(condition=Q(quantity__gt=0), name="orderitem_quantity_gt_zero")
        ]

    def __str__(self) -> str:
        return f"{self.quantity}x {self.product.sku} (Order {self.order.reference})"


class BoxRecommendation(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="recommendations")
    recommended_box = models.ForeignKey(
        Box,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recommendations",
    )
    result_status = models.CharField(max_length=50)
    payload = models.JSONField(help_text="Full audit explanation JSON")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        box_name = self.recommended_box.name if self.recommended_box else "None"
        return f"Recommendation for {self.order.reference}: {self.result_status} ({box_name})"
