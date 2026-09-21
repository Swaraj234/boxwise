import itertools
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Any


class RejectionReason(str, Enum):
    WEIGHT_EXCEEDED = "WEIGHT_EXCEEDED"
    VOLUME_EXCEEDED = "VOLUME_EXCEEDED"
    ITEM_TOO_LARGE = "ITEM_TOO_LARGE"
    NO_PACKING_FOUND = "NO_PACKING_FOUND"


@dataclass(frozen=True)
class Item:
    item_id: Any
    sku: str
    length: Decimal
    width: Decimal
    height: Decimal
    weight: Decimal

    @property
    def volume(self) -> Decimal:
        return self.length * self.width * self.height

    def all_orientations(self) -> list[tuple[Decimal, Decimal, Decimal]]:
        """
        Returns all unique 3D rotations (dim_x, dim_y, dim_z) for this item.
        At most 6 distinct permutations.
        """
        dims = (self.length, self.width, self.height)
        unique_orientations = sorted(set(itertools.permutations(dims)), reverse=True)
        return list(unique_orientations)


@dataclass(frozen=True)
class BoxSpec:
    box_id: Any
    name: str
    internal_length: Decimal
    internal_width: Decimal
    internal_height: Decimal
    max_weight: Decimal
    cost: Decimal

    @property
    def volume(self) -> Decimal:
        return self.internal_length * self.internal_width * self.internal_height


@dataclass
class Placement:
    item_id: Any
    sku: str
    x: Decimal
    y: Decimal
    z: Decimal
    dim_x: Decimal
    dim_y: Decimal
    dim_z: Decimal


@dataclass
class PackingResult:
    fits: bool
    placements: list[Placement]
    utilisation_volume_pct: Decimal
    utilisation_weight_pct: Decimal
    reason: RejectionReason | None = None
    detail: str | None = None


def validate_placements(box: BoxSpec, placements: list[Placement]) -> bool:
    """
    Independent verification function to guarantee ZERO false positives.
    Checks:
    1. Every placement fits strictly inside box bounds.
    2. No two placements overlap in 3D space (strict interior intersection).
    """
    zero = Decimal("0.00")
    for p in placements:
        if p.x < zero or p.y < zero or p.z < zero:
            return False
        if p.x + p.dim_x > box.internal_length:
            return False
        if p.y + p.dim_y > box.internal_width:
            return False
        if p.z + p.dim_z > box.internal_height:
            return False

    n = len(placements)
    for i in range(n):
        p1 = placements[i]
        for j in range(i + 1, n):
            p2 = placements[j]
            # Strict 3D bounding box overlap check
            overlap_x = max(p1.x, p2.x) < min(p1.x + p1.dim_x, p2.x + p2.dim_x)
            overlap_y = max(p1.y, p2.y) < min(p1.y + p1.dim_y, p2.y + p2.dim_y)
            overlap_z = max(p1.z, p2.z) < min(p1.z + p1.dim_z, p2.z + p2.dim_z)

            if overlap_x and overlap_y and overlap_z:
                return False

    return True


def pack_box(items: list[Item], box: BoxSpec) -> PackingResult:
    """
    Attempts to pack a list of items into a box using Extreme Points 3D heuristic.
    Executes fast pre-checks before attempting geometric placement.
    """
    zero_dec = Decimal("0.00")
    zero_weight = Decimal("0.000")

    total_weight = sum((item.weight for item in items), zero_weight)
    total_volume = sum((item.volume for item in items), zero_dec)

    # Calculate percentages relative to box limits
    weight_pct = (
        (total_weight / box.max_weight * Decimal("100.0")).quantize(Decimal("0.1"))
        if box.max_weight > zero_weight
        else Decimal("0.0")
    )
    vol_pct = (
        (total_volume / box.volume * Decimal("100.0")).quantize(Decimal("0.1"))
        if box.volume > zero_dec
        else Decimal("0.0")
    )

    # Pre-check 1: WEIGHT_EXCEEDED
    if total_weight > box.max_weight:
        return PackingResult(
            fits=False,
            placements=[],
            utilisation_volume_pct=vol_pct,
            utilisation_weight_pct=weight_pct,
            reason=RejectionReason.WEIGHT_EXCEEDED,
            detail=(
                f"Total item weight {total_weight:.3f} kg exceeds "
                f"box max weight {box.max_weight:.3f} kg."
            ),
        )

    # Pre-check 2: ITEM_TOO_LARGE
    box_dims_sorted = sorted([box.internal_length, box.internal_width, box.internal_height])
    for item in items:
        item_dims_sorted = sorted([item.length, item.width, item.height])
        if any(item_dims_sorted[i] > box_dims_sorted[i] for i in range(3)):
            return PackingResult(
                fits=False,
                placements=[],
                utilisation_volume_pct=vol_pct,
                utilisation_weight_pct=weight_pct,
                reason=RejectionReason.ITEM_TOO_LARGE,
                detail=(
                    f"Item {item.sku} ({item.length}x{item.width}x{item.height} cm) "
                    f"exceeds box internal dimensions in isolation."
                ),
            )

    # Pre-check 3: VOLUME_EXCEEDED
    if total_volume > box.volume:
        return PackingResult(
            fits=False,
            placements=[],
            utilisation_volume_pct=vol_pct,
            utilisation_weight_pct=weight_pct,
            reason=RejectionReason.VOLUME_EXCEEDED,
            detail=(
                f"Total item volume {total_volume:.2f} cm³ exceeds "
                f"box volume {box.volume:.2f} cm³."
            ),
        )

    # If no items provided, empty order fits trivially
    if not items:
        return PackingResult(
            fits=True,
            placements=[],
            utilisation_volume_pct=Decimal("0.0"),
            utilisation_weight_pct=Decimal("0.0"),
        )

    # Deterministic item sorting: volume DESC, max side DESC, item_id ASC
    sorted_items = sorted(
        items,
        key=lambda it: (
            -it.volume,
            -max(it.length, it.width, it.height),
            it.item_id,
        ),
    )

    # Extreme Points initialization
    extreme_points: set[tuple[Decimal, Decimal, Decimal]] = {(zero_dec, zero_dec, zero_dec)}
    placements: list[Placement] = []

    for item in sorted_items:
        placed = False
        # Candidate points ordered deterministically: z ASC, y ASC, x ASC
        candidate_points = sorted(extreme_points, key=lambda pt: (pt[2], pt[1], pt[0]))

        for px, py, pz in candidate_points:
            for dx, dy, dz in item.all_orientations():
                # Bounds check
                if (
                    px + dx > box.internal_length
                    or py + dy > box.internal_width
                    or pz + dz > box.internal_height
                ):
                    continue

                # 3D Overlap check against placed items
                overlap = False
                for pl in placements:
                    if (
                        max(px, pl.x) < min(px + dx, pl.x + pl.dim_x)
                        and max(py, pl.y) < min(py + dy, pl.y + pl.dim_y)
                        and max(pz, pl.z) < min(pz + dz, pl.z + pl.dim_z)
                    ):
                        overlap = True
                        break

                if overlap:
                    continue

                # Valid placement found!
                new_placement = Placement(
                    item_id=item.item_id,
                    sku=item.sku,
                    x=px,
                    y=py,
                    z=pz,
                    dim_x=dx,
                    dim_y=dy,
                    dim_z=dz,
                )
                placements.append(new_placement)
                placed = True

                # Generate new potential extreme points
                potential_points: set[tuple[Decimal, Decimal, Decimal]] = {
                    (px + dx, py, pz),
                    (px, py + dy, pz),
                    (px, py, pz + dz),
                }

                # Projections against existing placed items
                for pl in placements[:-1]:
                    if px + dx > pl.x and px + dx <= pl.x + pl.dim_x:
                        potential_points.add((px + dx, pl.y + pl.dim_y, pz))
                        potential_points.add((px + dx, py, pl.z + pl.dim_z))
                    if py + dy > pl.y and py + dy <= pl.y + pl.dim_y:
                        potential_points.add((pl.x + pl.dim_x, py + dy, pz))
                        potential_points.add((px, py + dy, pl.z + pl.dim_z))
                    if pz + dz > pl.z and pz + dz <= pl.z + pl.dim_z:
                        potential_points.add((pl.x + pl.dim_x, py, pz + dz))
                        potential_points.add((px, pl.y + pl.dim_y, pz + dz))

                # Add new potential points to set
                extreme_points.update(potential_points)

                # Filter out points that are inside placed boxes or out of box bounds
                filtered_points: set[tuple[Decimal, Decimal, Decimal]] = set()
                all_placements = placements

                for pt_x, pt_y, pt_z in extreme_points:
                    if (
                        pt_x >= box.internal_length
                        or pt_y >= box.internal_width
                        or pt_z >= box.internal_height
                    ):
                        continue

                    # Check if point lies strictly inside an existing box
                    inside_box = False
                    for pl in all_placements:
                        if (
                            pl.x <= pt_x < pl.x + pl.dim_x
                            and pl.y <= pt_y < pl.y + pl.dim_y
                            and pl.z <= pt_z < pl.z + pl.dim_z
                        ):
                            inside_box = True
                            break

                    if not inside_box:
                        filtered_points.add((pt_x, pt_y, pt_z))

                extreme_points = filtered_points
                break  # Exit orientation loop

            if placed:
                break  # Exit point search loop

        if not placed:
            return PackingResult(
                fits=False,
                placements=[],
                utilisation_volume_pct=vol_pct,
                utilisation_weight_pct=weight_pct,
                reason=RejectionReason.NO_PACKING_FOUND,
                detail=(
                    f"Box passed pre-checks, but geometric heuristic could not pack item "
                    f"{item.sku} ({item.length}x{item.width}x{item.height} cm)."
                ),
            )

    # Independent validation to guarantee zero false positives
    if not validate_placements(box, placements):
        raise RuntimeError("Generated invalid placements!")

    return PackingResult(
        fits=True,
        placements=placements,
        utilisation_volume_pct=vol_pct,
        utilisation_weight_pct=weight_pct,
        reason=None,
        detail=None,
    )
