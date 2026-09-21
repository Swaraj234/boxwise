from decimal import Decimal

from boxes.services.packing import BoxSpec, Item
from boxes.services.selection import select_box


class TestSelectionEngine:
    def test_cheapest_box_wins_over_smaller_expensive_box(self):
        box_cheap_large = BoxSpec(
            box_id=1,
            name="Cheap Large",
            internal_length=Decimal("30.00"),
            internal_width=Decimal("30.00"),
            internal_height=Decimal("30.00"),
            max_weight=Decimal("10.000"),
            cost=Decimal("1.50"),
        )
        box_expensive_small = BoxSpec(
            box_id=2,
            name="Expensive Small",
            internal_length=Decimal("20.00"),
            internal_width=Decimal("20.00"),
            internal_height=Decimal("20.00"),
            max_weight=Decimal("10.000"),
            cost=Decimal("2.50"),
        )
        item = Item(
            item_id="it-1",
            sku="SMALL-1",
            length=Decimal("10.00"),
            width=Decimal("10.00"),
            height=Decimal("10.00"),
            weight=Decimal("1.000"),
        )

        res = select_box([item], [box_expensive_small, box_cheap_large])
        assert res.status == "RECOMMENDED"
        assert res.recommended_box is not None
        assert res.recommended_box.box_id == 1  # Cheap Large wins ($1.50 vs $2.50)
        assert len(res.alternatives) == 1
        assert res.alternatives[0].box.box_id == 2

    def test_tie_break_smaller_volume(self):
        box_smaller_vol = BoxSpec(
            box_id=10,
            name="Box A (Smaller Vol)",
            internal_length=Decimal("20.00"),
            internal_width=Decimal("20.00"),
            internal_height=Decimal("20.00"),
            max_weight=Decimal("10.000"),
            cost=Decimal("2.00"),
        )
        box_larger_vol = BoxSpec(
            box_id=5,
            name="Box B (Larger Vol)",
            internal_length=Decimal("30.00"),
            internal_width=Decimal("20.00"),
            internal_height=Decimal("20.00"),
            max_weight=Decimal("10.000"),
            cost=Decimal("2.00"),
        )
        item = Item(
            "it-1",
            "PROD",
            Decimal("10.00"),
            Decimal("10.00"),
            Decimal("10.00"),
            Decimal("1.000"),
        )

        res = select_box([item], [box_larger_vol, box_smaller_vol])
        assert res.status == "RECOMMENDED"
        assert res.recommended_box is not None
        assert res.recommended_box.box_id == 10  # Smaller volume wins tie-break

    def test_tie_break_lowest_id(self):
        box_id_5 = BoxSpec(
            box_id=5,
            name="Box Five",
            internal_length=Decimal("20.00"),
            internal_width=Decimal("20.00"),
            internal_height=Decimal("20.00"),
            max_weight=Decimal("10.000"),
            cost=Decimal("2.00"),
        )
        box_id_2 = BoxSpec(
            box_id=2,
            name="Box Two",
            internal_length=Decimal("20.00"),
            internal_width=Decimal("20.00"),
            internal_height=Decimal("20.00"),
            max_weight=Decimal("10.000"),
            cost=Decimal("2.00"),
        )
        item = Item(
            "it-1",
            "PROD",
            Decimal("10.00"),
            Decimal("10.00"),
            Decimal("10.00"),
            Decimal("1.000"),
        )

        res = select_box([item], [box_id_5, box_id_2])
        assert res.status == "RECOMMENDED"
        assert res.recommended_box is not None
        assert res.recommended_box.box_id == 2  # Lowest box ID wins tie-break

    def test_alternatives_and_rejected_boxes_formatting(self):
        box_fit_1 = BoxSpec(
            1,
            "Box 1",
            Decimal("20.00"),
            Decimal("20.00"),
            Decimal("20.00"),
            Decimal("10.000"),
            Decimal("1.00"),
        )
        box_fit_2 = BoxSpec(
            2,
            "Box 2",
            Decimal("25.00"),
            Decimal("25.00"),
            Decimal("25.00"),
            Decimal("10.000"),
            Decimal("2.00"),
        )
        box_fit_3 = BoxSpec(
            3,
            "Box 3",
            Decimal("30.00"),
            Decimal("30.00"),
            Decimal("30.00"),
            Decimal("10.000"),
            Decimal("3.00"),
        )
        box_fit_4 = BoxSpec(
            4,
            "Box 4",
            Decimal("35.00"),
            Decimal("35.00"),
            Decimal("35.00"),
            Decimal("10.000"),
            Decimal("4.00"),
        )
        box_too_small = BoxSpec(
            99,
            "Tiny Box",
            Decimal("5.00"),
            Decimal("5.00"),
            Decimal("5.00"),
            Decimal("10.000"),
            Decimal("0.50"),
        )

        item = Item(
            "it-1",
            "ITEM-A",
            Decimal("10.00"),
            Decimal("10.00"),
            Decimal("10.00"),
            Decimal("1.000"),
        )

        res = select_box([item], [box_fit_4, box_fit_2, box_too_small, box_fit_1, box_fit_3])
        assert res.status == "RECOMMENDED"
        assert res.recommended_box is not None
        assert res.recommended_box.box_id == 1
        assert len(res.alternatives) == 2
        assert res.alternatives[0].box.box_id == 2
        assert res.alternatives[1].box.box_id == 3

        # Rejected box check
        assert len(res.rejected_boxes) == 1
        assert res.rejected_boxes[0].id == 99
        assert res.rejected_boxes[0].reason == "ITEM_TOO_LARGE"

    def test_no_single_box_fits(self):
        box_small = BoxSpec(
            1,
            "Small",
            Decimal("10.00"),
            Decimal("10.00"),
            Decimal("10.00"),
            Decimal("10.000"),
            Decimal("1.00"),
        )
        giant_item = Item(
            "it-1",
            "GIANT",
            Decimal("50.00"),
            Decimal("50.00"),
            Decimal("50.00"),
            Decimal("0.500"),
        )

        res = select_box([giant_item], [box_small])
        assert res.status == "NO_SINGLE_BOX_FITS"
        assert res.recommended_box is None
        assert res.recommended_result is None
        assert len(res.rejected_boxes) == 1
        assert res.rejected_boxes[0].reason == "ITEM_TOO_LARGE"
