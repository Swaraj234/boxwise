import random
import time
from decimal import Decimal

from boxes.services.packing import (
    BoxSpec,
    Item,
    RejectionReason,
    pack_box,
    validate_placements,
)


class TestPackingPreChecks:
    def test_weight_exceeded(self):
        box = BoxSpec(
            box_id=1,
            name="Small",
            internal_length=Decimal("20.00"),
            internal_width=Decimal("20.00"),
            internal_height=Decimal("20.00"),
            max_weight=Decimal("2.000"),
            cost=Decimal("1.00"),
        )
        heavy_item = Item(
            item_id="item-1",
            sku="HEAVY-1",
            length=Decimal("5.00"),
            width=Decimal("5.00"),
            height=Decimal("5.00"),
            weight=Decimal("2.500"),
        )
        res = pack_box([heavy_item], box)
        assert res.fits is False
        assert res.reason == RejectionReason.WEIGHT_EXCEEDED
        assert "exceeds box max weight" in res.detail

    def test_volume_exceeded(self):
        box = BoxSpec(
            box_id=1,
            name="Small",
            internal_length=Decimal("10.00"),
            internal_width=Decimal("10.00"),
            internal_height=Decimal("10.00"),  # Vol 1000
            max_weight=Decimal("50.000"),
            cost=Decimal("1.00"),
        )
        large_item = Item(
            item_id="item-1",
            sku="BIG-1",
            length=Decimal("11.00"),
            width=Decimal("10.00"),
            height=Decimal("10.00"),  # Vol 1100
            weight=Decimal("1.000"),
        )
        res = pack_box([large_item], box)
        assert res.fits is False
        assert res.reason in (RejectionReason.VOLUME_EXCEEDED, RejectionReason.ITEM_TOO_LARGE)

    def test_item_too_large(self):
        box = BoxSpec(
            box_id=1,
            name="Small",
            internal_length=Decimal("10.00"),
            internal_width=Decimal("10.00"),
            internal_height=Decimal("10.00"),
            max_weight=Decimal("50.000"),
            cost=Decimal("1.00"),
        )
        long_thin_item = Item(
            item_id="item-1",
            sku="LONG-1",
            length=Decimal("15.00"),
            width=Decimal("2.00"),
            height=Decimal("2.00"),
            weight=Decimal("0.500"),
        )
        res = pack_box([long_thin_item], box)
        assert res.fits is False
        assert res.reason == RejectionReason.ITEM_TOO_LARGE


class TestBoundariesAndRotations:
    def test_exact_fit_dimensions(self):
        box = BoxSpec(
            box_id=1,
            name="Exact",
            internal_length=Decimal("10.00"),
            internal_width=Decimal("10.00"),
            internal_height=Decimal("10.00"),
            max_weight=Decimal("5.000"),
            cost=Decimal("1.00"),
        )
        item_exact = Item(
            item_id="exact-1",
            sku="EXACT",
            length=Decimal("10.00"),
            width=Decimal("10.00"),
            height=Decimal("10.00"),
            weight=Decimal("5.000"),
        )
        res = pack_box([item_exact], box)
        assert res.fits is True
        assert len(res.placements) == 1
        assert validate_placements(box, res.placements) is True

    def test_item_point_01_cm_too_large(self):
        box = BoxSpec(
            box_id=1,
            name="Exact",
            internal_length=Decimal("10.00"),
            internal_width=Decimal("10.00"),
            internal_height=Decimal("10.00"),
            max_weight=Decimal("5.000"),
            cost=Decimal("1.00"),
        )
        item_over = Item(
            item_id="over-1",
            sku="OVER",
            length=Decimal("10.01"),
            width=Decimal("10.00"),
            height=Decimal("10.00"),
            weight=Decimal("1.000"),
        )
        res = pack_box([item_over], box)
        assert res.fits is False
        assert res.reason == RejectionReason.ITEM_TOO_LARGE

    def test_weight_exact_and_over(self):
        box = BoxSpec(
            box_id=1,
            name="Box",
            internal_length=Decimal("20.00"),
            internal_width=Decimal("20.00"),
            internal_height=Decimal("20.00"),
            max_weight=Decimal("5.000"),
            cost=Decimal("1.00"),
        )
        item_exact_weight = Item(
            item_id="w-exact",
            sku="W-EXACT",
            length=Decimal("5.00"),
            width=Decimal("5.00"),
            height=Decimal("5.00"),
            weight=Decimal("5.000"),
        )
        res_exact = pack_box([item_exact_weight], box)
        assert res_exact.fits is True

        item_over_weight = Item(
            item_id="w-over",
            sku="W-OVER",
            length=Decimal("5.00"),
            width=Decimal("5.00"),
            height=Decimal("5.00"),
            weight=Decimal("5.001"),
        )
        res_over = pack_box([item_over_weight], box)
        assert res_over.fits is False
        assert res_over.reason == RejectionReason.WEIGHT_EXCEEDED

    def test_item_fits_only_when_rotated(self):
        # Box is 10 x 20 x 5
        box = BoxSpec(
            box_id=1,
            name="OrientBox",
            internal_length=Decimal("10.00"),
            internal_width=Decimal("20.00"),
            internal_height=Decimal("5.00"),
            max_weight=Decimal("10.000"),
            cost=Decimal("1.00"),
        )
        # Item natural dims (20x10x5) fail length=10, but fit when rotated to 10x20x5
        item_rotate = Item(
            item_id="rot-1",
            sku="ROTATE-ME",
            length=Decimal("20.00"),
            width=Decimal("10.00"),
            height=Decimal("5.00"),
            weight=Decimal("1.000"),
        )
        res = pack_box([item_rotate], box)
        assert res.fits is True
        pl = res.placements[0]
        assert pl.dim_x <= box.internal_length
        assert pl.dim_y <= box.internal_width
        assert pl.dim_z <= box.internal_height
        assert validate_placements(box, res.placements) is True


class TestGeometryNoFitAndDeterminism:
    def test_volume_fits_geometry_fails(self):
        # Box 15 x 15 x 15 (Vol = 3375)
        box = BoxSpec(
            box_id=1,
            name="Cube",
            internal_length=Decimal("15.00"),
            internal_width=Decimal("15.00"),
            internal_height=Decimal("15.00"),
            max_weight=Decimal("50.000"),
            cost=Decimal("1.00"),
        )
        # Two 10 x 10 x 10 items (Total Vol = 2000 < 3375, but cannot both fit along 15cm axes)
        items = [
            Item(
                "i-1",
                "CUBE-1",
                Decimal("10.00"),
                Decimal("10.00"),
                Decimal("10.00"),
                Decimal("1.000"),
            ),
            Item(
                "i-2",
                "CUBE-2",
                Decimal("10.00"),
                Decimal("10.00"),
                Decimal("10.00"),
                Decimal("1.000"),
            ),
        ]
        res = pack_box(items, box)
        assert res.fits is False
        assert res.reason == RejectionReason.NO_PACKING_FOUND

    def test_determinism_under_shuffled_input(self):
        box = BoxSpec(
            box_id=1,
            name="DetBox",
            internal_length=Decimal("30.00"),
            internal_width=Decimal("30.00"),
            internal_height=Decimal("30.00"),
            max_weight=Decimal("50.000"),
            cost=Decimal("1.00"),
        )
        items = [
            Item(
                "i-1", "MED", Decimal("10.00"), Decimal("10.00"), Decimal("10.00"), Decimal("1.000")
            ),
            Item(
                "i-2",
                "LARGE",
                Decimal("15.00"),
                Decimal("15.00"),
                Decimal("15.00"),
                Decimal("2.000"),
            ),
            Item(
                "i-3", "SMALL", Decimal("5.00"), Decimal("5.00"), Decimal("5.00"), Decimal("0.500")
            ),
        ]

        res1 = pack_box(items, box)
        assert res1.fits is True

        # Shuffle item input order multiple times
        for seed in range(5):
            shuffled = list(items)
            random.seed(seed)
            random.shuffle(shuffled)
            res_shuffled = pack_box(shuffled, box)
            assert res_shuffled.fits is True
            # Assert exact placement coordinates match
            coords1 = [
                (p.item_id, p.x, p.y, p.z, p.dim_x, p.dim_y, p.dim_z) for p in res1.placements
            ]
            coords2 = [
                (p.item_id, p.x, p.y, p.z, p.dim_x, p.dim_y, p.dim_z)
                for p in res_shuffled.placements
            ]
            assert sorted(coords1) == sorted(coords2)

    def test_identical_items_ascending_item_id_order(self):
        box = BoxSpec(
            box_id=1,
            name="Box",
            internal_length=Decimal("30.00"),
            internal_width=Decimal("10.00"),
            internal_height=Decimal("10.00"),
            max_weight=Decimal("10.000"),
            cost=Decimal("1.00"),
        )
        # 3 identical items passed in order 3, 1, 2
        item3 = Item(
            item_id=3,
            sku="CUBE",
            length=Decimal("10.00"),
            width=Decimal("10.00"),
            height=Decimal("10.00"),
            weight=Decimal("1.000"),
        )
        item1 = Item(
            item_id=1,
            sku="CUBE",
            length=Decimal("10.00"),
            width=Decimal("10.00"),
            height=Decimal("10.00"),
            weight=Decimal("1.000"),
        )
        item2 = Item(
            item_id=2,
            sku="CUBE",
            length=Decimal("10.00"),
            width=Decimal("10.00"),
            height=Decimal("10.00"),
            weight=Decimal("1.000"),
        )

        res = pack_box([item3, item1, item2], box)
        assert res.fits is True
        # Identical items must be placed in ascending item_id order: 1, then 2, then 3
        placed_ids = [p.item_id for p in res.placements]
        assert placed_ids == [1, 2, 3]


class TestPerformance:
    def test_pack_200_small_items_under_time_limit(self):
        # 50 x 50 x 50 box
        box = BoxSpec(
            box_id=99,
            name="BigBox",
            internal_length=Decimal("50.00"),
            internal_width=Decimal("50.00"),
            internal_height=Decimal("50.00"),
            max_weight=Decimal("500.000"),
            cost=Decimal("10.00"),
        )
        # 200 items of size 4 x 4 x 4 cm
        items = [
            Item(
                item_id=f"small-{i}",
                sku="TINY",
                length=Decimal("4.00"),
                width=Decimal("4.00"),
                height=Decimal("4.00"),
                weight=Decimal("0.100"),
            )
            for i in range(200)
        ]

        start_time = time.perf_counter()
        res = pack_box(items, box)
        elapsed = time.perf_counter() - start_time

        assert res.fits is True
        assert len(res.placements) == 200
        assert validate_placements(box, res.placements) is True
        assert elapsed < 2.0, f"Packing 200 items took {elapsed:.2f}s (must be < 2.0s)"
