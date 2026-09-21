from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from boxes.models import Box, Order, OrderItem, Product


class Command(BaseCommand):
    help = "Seeds the database with realistic sample products, shipping boxes, and demo orders."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete existing products, boxes, and orders before seeding.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["clear"]:
            self.stdout.write("Clearing existing database records...")
            OrderItem.objects.all().delete()
            Order.objects.all().delete()
            Product.objects.all().delete()
            Box.objects.all().delete()
            self.stdout.write(self.style.WARNING("Existing data cleared."))

        self.stdout.write("Seeding sample Products...")
        products_data = [
            {
                "sku": "PROD-BOOK",
                "name": "Hardcover Book",
                "length": Decimal("24.00"),
                "width": Decimal("17.00"),
                "height": Decimal("3.50"),
                "weight": Decimal("0.850"),
                "is_active": True,
            },
            {
                "sku": "PROD-MUG",
                "name": "Ceramic Coffee Mug",
                "length": Decimal("12.00"),
                "width": Decimal("10.00"),
                "height": Decimal("10.00"),
                "weight": Decimal("0.450"),
                "is_active": True,
            },
            {
                "sku": "PROD-TSHIRT",
                "name": "Folded Apparel T-Shirt",
                "length": Decimal("25.00"),
                "width": Decimal("20.00"),
                "height": Decimal("2.00"),
                "weight": Decimal("0.200"),
                "is_active": True,
            },
            {
                "sku": "PROD-LAPTOP",
                "name": '15" Premium Laptop',
                "length": Decimal("36.00"),
                "width": Decimal("25.00"),
                "height": Decimal("2.00"),
                "weight": Decimal("2.100"),
                "is_active": True,
            },
            {
                "sku": "PROD-HEADPHONES",
                "name": "Wireless Noise-Canceling Headphones",
                "length": Decimal("20.00"),
                "width": Decimal("18.00"),
                "height": Decimal("8.00"),
                "weight": Decimal("0.600"),
                "is_active": True,
            },
            {
                "sku": "PROD-SHOES",
                "name": "Athletic Running Shoes",
                "length": Decimal("33.00"),
                "width": Decimal("21.00"),
                "height": Decimal("12.00"),
                "weight": Decimal("1.100"),
                "is_active": True,
            },
            {
                "sku": "PROD-PEN",
                "name": "Luxury Executive Pen Set",
                "length": Decimal("18.00"),
                "width": Decimal("6.00"),
                "height": Decimal("3.00"),
                "weight": Decimal("0.150"),
                "is_active": True,
            },
        ]

        products_map = {}
        for pdata in products_data:
            prod, created = Product.objects.update_or_create(sku=pdata["sku"], defaults=pdata)
            products_map[prod.sku] = prod
            status_str = "Created" if created else "Updated"
            self.stdout.write(f"  [{status_str}] Product {prod.sku} ({prod.name})")

        self.stdout.write("\nSeeding sample Boxes...")
        boxes_data = [
            {
                "name": "Mailer Envelope",
                "internal_length": Decimal("30.00"),
                "internal_width": Decimal("22.00"),
                "internal_height": Decimal("5.00"),
                "max_weight": Decimal("2.000"),
                "empty_weight": Decimal("0.050"),
                "cost": Decimal("0.50"),
                "is_active": True,
            },
            {
                "name": "Small Shipping Box",
                "internal_length": Decimal("25.00"),
                "internal_width": Decimal("20.00"),
                "internal_height": Decimal("15.00"),
                "max_weight": Decimal("5.000"),
                "empty_weight": Decimal("0.150"),
                "cost": Decimal("1.20"),
                "is_active": True,
            },
            {
                "name": "Medium Shipping Box",
                "internal_length": Decimal("35.00"),
                "internal_width": Decimal("28.00"),
                "internal_height": Decimal("20.00"),
                "max_weight": Decimal("10.000"),
                "empty_weight": Decimal("0.300"),
                "cost": Decimal("2.10"),
                "is_active": True,
            },
            {
                "name": "Large Shipping Box",
                "internal_length": Decimal("45.00"),
                "internal_width": Decimal("35.00"),
                "internal_height": Decimal("30.00"),
                "max_weight": Decimal("20.000"),
                "empty_weight": Decimal("0.500"),
                "cost": Decimal("3.80"),
                "is_active": True,
            },
            {
                "name": "Extra Large Box",
                "internal_length": Decimal("60.00"),
                "internal_width": Decimal("45.00"),
                "internal_height": Decimal("40.00"),
                "max_weight": Decimal("30.000"),
                "empty_weight": Decimal("0.800"),
                "cost": Decimal("5.50"),
                "is_active": True,
            },
        ]

        for bdata in boxes_data:
            box, created = Box.objects.update_or_create(name=bdata["name"], defaults=bdata)
            status_str = "Created" if created else "Updated"
            self.stdout.write(f"  [{status_str}] Box {box.name} (${box.cost})")

        self.stdout.write("\nSeeding sample Orders...")
        orders_data = [
            {
                "reference": "ORD-DEMO-001",
                "items": [
                    {"sku": "PROD-BOOK", "quantity": 2},
                    {"sku": "PROD-MUG", "quantity": 1},
                ],
            },
            {
                "reference": "ORD-DEMO-002",
                "items": [
                    {"sku": "PROD-LAPTOP", "quantity": 1},
                    {"sku": "PROD-HEADPHONES", "quantity": 1},
                ],
            },
        ]

        for odata in orders_data:
            order, created = Order.objects.get_or_create(reference=odata["reference"])
            if not created:
                order.items.all().delete()

            for item_info in odata["items"]:
                prod = products_map[item_info["sku"]]
                OrderItem.objects.create(order=order, product=prod, quantity=item_info["quantity"])

            status_str = "Created" if created else "Updated"
            self.stdout.write(f"  [{status_str}] Order {order.reference}")

        self.stdout.write(self.style.SUCCESS("\nDemo data seeded successfully!"))
