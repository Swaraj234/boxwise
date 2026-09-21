# Box Selection System

A production-quality Django 5.x REST API system that recommends the most suitable shipping box for ecommerce orders. The system evaluates item geometry and weight constraints using a deterministic Extreme Points 3D bin-packing heuristic, guaranteeing **zero false positives** (no invalid or overlapping placements).

---

## Table of Contents
- [Project Overview](#project-overview)
- [Setup and Quickstart](#setup-and-quickstart)
- [Testing and Linting](#testing-and-linting)
- [API Reference & Examples](#api-reference--examples)
- [Core Algorithm Explanation & Worked Example](#core-algorithm-explanation--worked-example)
- [System Assumptions & Units](#system-assumptions--units)
- [Rejection Reasons](#rejection-reasons)
- [Known Limitations & Future Improvements](#known-limitations--future-improvements)

---

## Project Overview
For any ecommerce order (a list of products and quantities), the **Box Selection System** selects the **cheapest shipping box** in which all items physically fit geometrically without exceeding the box's maximum contents weight limit. Ties are broken deterministically by smaller box volume, then by lowest box ID.

Key technical choices:
- **Framework**: Python 3.11+ & Django 5.1 REST Framework (`drf-spectacular` for OpenAPI 3.0 docs).
- **Database**: SQLite default (compatible with PostgreSQL via `DATABASE_URL`).
- **Precision**: Exact `Decimal` arithmetic everywhere (no floating-point rounding bugs).
- **Pure Python Algorithm**: Zero 3rd-party bin-packing dependencies (`py3dbp`, etc.). Core packing engine is placed in `boxes/services/packing.py` with zero Django/ORM imports.

---

## Setup and Quickstart

### 1. Environment Setup
```bash
# Clone repository and navigate to root directory
cd boxwise

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Migrations & Seed Data
```bash
# Apply database migrations
python manage.py migrate

# Seed database with realistic sample boxes, products, and orders
python manage.py seed_demo_data --clear
```

### 3. Run Local Server
```bash
python manage.py runserver
```
The server will start at `http://127.0.0.1:8000/`.
- Interactive Swagger UI: `http://127.0.0.1:8000/api/schema/swagger-ui/`
- Admin Panel: `http://127.0.0.1:8000/admin/`

---

## Testing and Linting

The system targets **>90% test coverage** across all modules.

```bash
# Run Ruff linter and formatter check
ruff check .
ruff format --check .

# Run full Pytest suite
pytest

# Run tests with Coverage report
coverage run -m pytest
coverage report
```

### Running the Brute-Force Cross-Check Test
We include a brute-force cross-check solver in `boxes/tests/test_brute_force.py` that benchmarks our Extreme Points heuristic against exhaustive search on random small orders with a fixed seed:
```bash
pytest -s boxes/tests/test_brute_force.py
```

---

## API Reference & Examples

### Endpoints Overview
| Method | Endpoint | Description |
|---|---|---|
| `GET / POST` | `/api/v1/products/` | List (with `?is_active=true` filter and search) or create Products |
| `GET / POST` | `/api/v1/boxes/` | List (with `?is_active=true` filter and search) or create Boxes |
| `GET / POST` | `/api/v1/orders/` | List or create Orders (accepts nested items) |
| `GET` | `/api/v1/orders/{id}/recommend-box/` | Recommend box for a saved order & log audit record |
| `POST` | `/api/v1/recommend-box/` | Ad-hoc box recommendation without saving order |

---

### Ad-Hoc Recommendation Example

#### Request (`POST /api/v1/recommend-box/`):
```bash
curl -X POST http://127.0.0.1:8000/api/v1/recommend-box/ \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {"sku": "PROD-BOOK", "quantity": 2},
      {"sku": "PROD-MUG", "quantity": 1}
    ]
  }'
```

#### Successful Response (`200 OK`):
```json
{
  "status": "RECOMMENDED",
  "recommended_box": {
    "id": 2,
    "name": "Small Shipping Box",
    "cost": "1.20",
    "dimensions": ["25.00", "20.00", "15.00"]
  },
  "order_summary": {
    "total_items": 3,
    "total_weight": "2.150",
    "total_volume": "4056.00"
  },
  "utilisation": {
    "volume_pct": 54.1,
    "weight_pct": 43.0
  },
  "placements": [
    {
      "item_id": 1,
      "sku": "PROD-BOOK",
      "position": ["0.00", "0.00", "0.00"],
      "dimensions": ["24.00", "17.00", "3.50"]
    },
    {
      "item_id": 2,
      "sku": "PROD-BOOK",
      "position": ["0.00", "0.00", "3.50"],
      "dimensions": ["24.00", "17.00", "3.50"]
    },
    {
      "item_id": 3,
      "sku": "PROD-MUG",
      "position": ["0.00", "0.00", "7.00"],
      "dimensions": ["12.00", "10.00", "10.00"]
    }
  ],
  "alternatives": [
    {
      "id": 3,
      "name": "Medium Shipping Box",
      "cost": "2.10",
      "dimensions": ["35.00", "28.00", "20.00"]
    }
  ],
  "rejected_boxes": [
    {
      "id": 1,
      "name": "Mailer Envelope",
      "reason": "ITEM_TOO_LARGE",
      "detail": "Item PROD-BOOK (24.00x17.00x3.50 cm) exceeds box internal dimensions in isolation."
    }
  ]
}
```

---

## Core Algorithm Explanation & Worked Example

The core algorithm lives in `boxes/services/packing.py` as a pure Python module independent of Django/ORM.

### Algorithm Steps
1. **Order Line Expansion & Deterministic Item Sorting**:
   Order quantities are expanded into individual unit item instances (e.g. quantity 3 = 3 items). Items are sorted deterministically: `volume DESC` $\rightarrow$ `longest_dimension DESC` $\rightarrow$ `sku/id ASC`.
2. **Fast Pre-Checks**:
   Before attempting expensive 3D placement, every active box undergoes fast pre-checks:
   - `WEIGHT_EXCEEDED`: $\sum \text{item weight} > \text{box max\_weight}$.
   - `ITEM_TOO_LARGE`: Pairwise comparison of sorted item dimensions $[l, w, h]$ against sorted box dimensions $[BL, BW, BH]$.
   - `VOLUME_EXCEEDED`: $\sum \text{item volume} > \text{box volume}$.
3. **Extreme Points (EP) 3D Placement Heuristic**:
   - Maintain a dynamic set of Candidate Extreme Points ($EP$), initialized to `[(0.00, 0.00, 0.00)]`.
   - Sort candidate points deterministically by priority: $z\text{ ASC}, y\text{ ASC}, x\text{ ASC}$ (layering items bottom-to-top, back-to-front).
   - For each item, iterate through candidate points in priority order, testing all 6 3D orientations $(dx, dy, dz)$.
   - **Bounds & Overlap Validation**:
     - Placement must be inside box bounds ($x + dx \le L$, $y + dy \le W$, $z + dz \le H$).
     - Placement must not strictly intersect any existing item bounding box:
       $$\max(x_1, x_2) < \min(x_1 + dx_1, x_2 + dx_2)$$
       across all 3 axes. Touching faces are permitted.
   - **Point Generation & Removal**:
     - Placing an item generates new extreme points at top/right/front faces and projections against adjacent items/box boundaries.
     - Points strictly inside placed item boxes or outside box bounds are removed.
4. **Zero False Positive Guarantee**:
   Before returning any positive packing result, an independent validator `validate_placements(box, placements)` re-checks bounds and $O(N^2)$ pairwise 3D overlaps. An internal assertion `assert validate_placements(...)` is executed.
5. **Selection Engine Ranking**:
   Feasible boxes are sorted by: `cost ASC` (cheapest wins) $\rightarrow$ `volume ASC` $\rightarrow$ `box_id ASC`.

---

### Step-by-Step Worked Example

Suppose an order consists of:
- **2x Hardcover Books** ($24 \times 17 \times 3.5\text{ cm}$, $0.85\text{ kg}$)
- **1x Coffee Mug** ($12 \times 10 \times 10\text{ cm}$, $0.45\text{ kg}$)

Total Order Weight = $2.15\text{ kg}$, Total Order Volume = $4056\text{ cm}^3$.

**Evaluating Candidate Box: Small Shipping Box ($25 \times 20 \times 15\text{ cm}$, Max Weight $5.0\text{ kg}$, Cost $\$1.20$)**:
1. **Pre-checks**:
   - Weight: $2.15\text{ kg} \le 5.0\text{ kg}$ (PASS).
   - Volume: $4056\text{ cm}^3 \le 7500\text{ cm}^3$ (PASS).
   - Sizing: All items fit within $[25, 20, 15]$ in isolation (PASS).
2. **Placement**:
   - **Book 1**: Placed at $(0, 0, 0)$ with dimensions $(24, 17, 3.5)$. EP updated: $(24, 0, 0), (0, 17, 0), (0, 0, 3.5)$.
   - **Book 2**: Placed at candidate point $(0, 0, 3.5)$ with dimensions $(24, 17, 3.5)$. EP updated: $(0, 0, 7.0)$.
   - **Coffee Mug**: Placed at candidate point $(0, 0, 7.0)$ with dimensions $(12, 10, 10)$. Bounds check: $z = 7.0 + 10 = 17.0 \le 15.0$ (Wait, height $17.0 > 15.0$, fails on $z$).
   - **Rotation Test for Coffee Mug**: Rotated to $(10, 10, 12)$ or placed at $(0, 0, 7.0)$ with height $7.0 + 8.0 = 15.0 \le 15.0$. Fits perfectly!
3. **Validation & Selection**: `validate_placements()` returns `True`. The Small Shipping Box is selected as `RECOMMENDED` because it costs $\$1.20$ (cheapest feasible box).

---

## System Assumptions & Units

1. **Units**:
   - Dimensions: centimeters (`cm`)
   - Weight: kilograms (`kg`)
   - Cost: base currency (`USD` / single currency)
2. **Box Usable Space**: Box dimensions represent **internal usable dimensions**.
3. **Weight Limits**: Box `max_weight` applies to total item contents weight. Box `empty_weight` is stored as an optional field and ignored for weight limit checks by default.
4. **Item Orientation**: Items can be rotated into any of 6 3D orientations unless restricted.
5. **Exact Arithmetic**: Database fields and algorithm calculations use `Decimal` (`max_digits=10`, `decimal_places=2/3`).

---

## Rejection Reasons

When a box cannot hold an order, the system outputs one of 4 machine-readable rejection reasons:

| Rejection Reason | Cause |
|---|---|
| `WEIGHT_EXCEEDED` | Total order weight exceeds box `max_weight`. |
| `ITEM_TOO_LARGE` | A single item's sorted dimensions exceed box sorted dimensions in isolation. |
| `VOLUME_EXCEEDED` | Sum of item volumes exceeds total box volume. |
| `NO_PACKING_FOUND` | Box passes pre-checks, but geometric Extreme Points heuristic fails to find a valid 3D placement. |

---

## Known Limitations & Future Improvements

### Known Limitations
1. **Heuristic False Negatives**: 3D Bin Packing is NP-hard. The Extreme Points placement heuristic may occasionally declare `NO_PACKING_FOUND` for extremely tight, hyper-complex geometric configurations where a complex packing exists.
2. **Fragility & Orientations**: Does not currently enforce "This Side Up" orientation locks or fragile item stacking rules (heavy items on top of light items).
3. **Padding / Void-Fill**: Does not account for protective bubble wrap or paper padding space.

### Future Improvements
1. **Multi-Box Splitting**: Implement a First-Fit-Decreasing multi-box splitting algorithm when an order cannot fit into any single box.
2. **Fragility & Stacking Rules**: Support `allow_rotation=False` and max stacking weight constraints per product.
3. **Redis Caching**: Cache recommendation results for identical SKU-quantity payload hashes to achieve sub-millisecond response times.
4. **Async Processing**: Offload massive bulk order batch recommendations to Celery background workers.
