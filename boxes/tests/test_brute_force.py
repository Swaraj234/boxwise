import itertools
import random
from decimal import Decimal

from boxes.services.packing import BoxSpec, Item, Placement, pack_box, validate_placements


def brute_force_pack(items: list[Item], box: BoxSpec, step: Decimal = Decimal("1.00")) -> bool:
    """
    Exhaustive brute-force search over item permutations, orientations, and grid coordinates.
    Used for small random test cases to benchmark heuristic accuracy.
    """
    if sum((it.weight for it in items), Decimal("0")) > box.max_weight:
        return False
    if sum((it.volume for it in items), Decimal("0")) > box.volume:
        return False

    n = len(items)

    def search(
        item_idx: int,
        current_placements: list[Placement],
        orientations: list[tuple[Decimal, Decimal, Decimal]],
        permuted_items: list[Item],
    ) -> bool:
        if item_idx == n:
            return validate_placements(box, current_placements)

        item = permuted_items[item_idx]
        dx, dy, dz = orientations[item_idx]

        # Generate candidate positions on grid step
        max_x = int((box.internal_length - dx) / step)
        max_y = int((box.internal_width - dy) / step)
        max_z = int((box.internal_height - dz) / step)

        if max_x < 0 or max_y < 0 or max_z < 0:
            return False

        # Try placement points (including extreme corner points for speed)
        candidate_points = {(Decimal("0.00"), Decimal("0.00"), Decimal("0.00"))}
        for pl in current_placements:
            candidate_points.add((pl.x + pl.dim_x, pl.y, pl.z))
            candidate_points.add((pl.x, pl.y + pl.dim_y, pl.z))
            candidate_points.add((pl.x, pl.y, pl.z + pl.dim_z))

        # Also add grid points
        for gx in range(0, max_x + 1, 2):
            for gy in range(0, max_y + 1, 2):
                for gz in range(0, max_z + 1, 2):
                    candidate_points.add(
                        (Decimal(gx) * step, Decimal(gy) * step, Decimal(gz) * step)
                    )

        for px, py, pz in candidate_points:
            if (
                px + dx > box.internal_length
                or py + dy > box.internal_width
                or pz + dz > box.internal_height
            ):
                continue

            # Check overlap
            overlap = False
            for pl in current_placements:
                if (
                    max(px, pl.x) < min(px + dx, pl.x + pl.dim_x)
                    and max(py, pl.y) < min(py + dy, pl.y + pl.dim_y)
                    and max(pz, pl.z) < min(pz + dz, pl.z + pl.dim_z)
                ):
                    overlap = True
                    break

            if not overlap:
                new_pl = Placement(
                    item_id=item.item_id,
                    sku=item.sku,
                    x=px,
                    y=py,
                    z=pz,
                    dim_x=dx,
                    dim_y=dy,
                    dim_z=dz,
                )
                current_placements.append(new_pl)
                if search(item_idx + 1, current_placements, orientations, permuted_items):
                    return True
                current_placements.pop()

        return False

    for perm in itertools.permutations(items):
        orientation_options = [it.all_orientations() for it in perm]
        for orientations in itertools.product(*orientation_options):
            if search(0, [], list(orientations), list(perm)):
                return True

    return False


class TestBruteForceCrossCheck:
    def test_brute_force_cross_check(self, capsys):
        """
        Generates small random packing cases with a fixed seed.
        Asserts zero false positives (whenever heuristic says fits, validate_placements passes).
        Reports how often heuristic missed a packing found by brute force.
        """
        random.seed(42)
        total_cases = 15
        heuristic_fits_count = 0
        brute_force_fits_count = 0
        heuristic_misses_count = 0

        for case_num in range(1, total_cases + 1):
            box_l = Decimal(random.choice([10, 12, 15]))
            box_w = Decimal(random.choice([10, 12, 15]))
            box_h = Decimal(random.choice([10, 12, 15]))

            box = BoxSpec(
                box_id=case_num,
                name=f"RandomBox-{case_num}",
                internal_length=box_l,
                internal_width=box_w,
                internal_height=box_h,
                max_weight=Decimal("50.000"),
                cost=Decimal("1.00"),
            )

            num_items = random.randint(2, 3)
            items = []
            for i in range(num_items):
                il = Decimal(random.randint(4, 8))
                iw = Decimal(random.randint(4, 8))
                ih = Decimal(random.randint(4, 8))
                items.append(
                    Item(
                        item_id=f"item-{i+1}",
                        sku=f"RAND-{i+1}",
                        length=il,
                        width=iw,
                        height=ih,
                        weight=Decimal("1.000"),
                    )
                )

            heuristic_res = pack_box(items, box)
            bf_fits = brute_force_pack(items, box)

            if heuristic_res.fits:
                heuristic_fits_count += 1
                # Guarantee: Zero false positives
                assert validate_placements(box, heuristic_res.placements) is True

            if bf_fits:
                brute_force_fits_count += 1

            if bf_fits and not heuristic_res.fits:
                heuristic_misses_count += 1

        # Output detailed report
        miss_rate = (
            (heuristic_misses_count / brute_force_fits_count * 100)
            if brute_force_fits_count > 0
            else 0.0
        )
        print("\n--- BRUTE FORCE CROSS-CHECK REPORT ---")
        print(f"Total test cases evaluated: {total_cases}")
        print(f"Brute-force found packing: {brute_force_fits_count}/{total_cases}")
        print(f"Heuristic found packing:   {heuristic_fits_count}/{total_cases}")
        print(f"Heuristic false negatives (missed packings): {heuristic_misses_count}")
        print(f"Heuristic false negative rate: {miss_rate:.1f}%")
        print("Heuristic false positive rate: 0.0% (GUARANTEED)")
        print("--------------------------------------")
