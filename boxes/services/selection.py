from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from .packing import BoxSpec, Item, PackingResult, pack_box


@dataclass
class RejectedBoxInfo:
    id: Any
    name: str
    reason: str
    detail: str


@dataclass
class AlternativeBoxInfo:
    box: BoxSpec
    packing_result: PackingResult


@dataclass
class OrderSummary:
    total_items: int
    total_weight: Decimal
    total_volume: Decimal


@dataclass
class SelectionResult:
    status: str  # "RECOMMENDED" or "NO_SINGLE_BOX_FITS"
    recommended_box: BoxSpec | None
    recommended_result: PackingResult | None
    order_summary: OrderSummary
    utilisation: dict[str, float]
    placements: list[Any]
    alternatives: list[AlternativeBoxInfo]
    rejected_boxes: list[RejectedBoxInfo] = field(default_factory=list)


def select_box(items: list[Item], boxes: list[BoxSpec]) -> SelectionResult:
    """
    Selects the optimal shipping box for a set of items from a list of candidate boxes.
    Feasible boxes are sorted by:
      1. Cost ASC (cheapest box wins)
      2. Volume ASC (tie-break 1: smaller box volume)
      3. Box ID ASC (tie-break 2: lowest box ID)
    """
    zero_dec = Decimal("0.00")
    zero_weight = Decimal("0.000")

    total_items = len(items)
    total_weight = sum((it.weight for it in items), zero_weight)
    total_volume = sum((it.volume for it in items), zero_dec)

    summary = OrderSummary(
        total_items=total_items,
        total_weight=total_weight,
        total_volume=total_volume,
    )

    feasible_boxes: list[tuple[BoxSpec, PackingResult]] = []
    rejected_boxes: list[RejectedBoxInfo] = []

    for box in boxes:
        result = pack_box(items, box)
        if result.fits:
            feasible_boxes.append((box, result))
        else:
            rejected_boxes.append(
                RejectedBoxInfo(
                    id=box.box_id,
                    name=box.name,
                    reason=result.reason.value if result.reason else "UNKNOWN",
                    detail=result.detail or "",
                )
            )

    if not feasible_boxes:
        return SelectionResult(
            status="NO_SINGLE_BOX_FITS",
            recommended_box=None,
            recommended_result=None,
            order_summary=summary,
            utilisation={"volume_pct": 0.0, "weight_pct": 0.0},
            placements=[],
            alternatives=[],
            rejected_boxes=rejected_boxes,
        )

    # Sort feasible boxes deterministically: cost ASC, volume ASC, box_id ASC
    feasible_boxes.sort(key=lambda pair: (pair[0].cost, pair[0].volume, pair[0].box_id))

    best_box, best_result = feasible_boxes[0]
    alternative_pairs = feasible_boxes[1:3]

    alternatives = [AlternativeBoxInfo(box=b, packing_result=r) for b, r in alternative_pairs]

    utilisation = {
        "volume_pct": float(best_result.utilisation_volume_pct),
        "weight_pct": float(best_result.utilisation_weight_pct),
    }

    return SelectionResult(
        status="RECOMMENDED",
        recommended_box=best_box,
        recommended_result=best_result,
        order_summary=summary,
        utilisation=utilisation,
        placements=best_result.placements,
        alternatives=alternatives,
        rejected_boxes=rejected_boxes,
    )
