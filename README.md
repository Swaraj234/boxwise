# Box Selection System

A production-quality Django 5.x REST API that recommends the most suitable shipping box for ecommerce orders.

The system evaluates product dimensions, item quantities, total weight, and box capacity using a deterministic Extreme Points 3D bin-packing heuristic.

The packing engine is designed with a **zero-false-positive guarantee**: whenever it reports that an order fits inside a box, the resulting placements are independently validated for bounds and pairwise overlap.

> **Important:** The packing algorithm is a deterministic heuristic, not an exact 3D bin-packing solver. It may report that an order does not fit even when a more sophisticated packing arrangement might exist.

---

## Table of Contents

* [Project Overview](#project-overview)
* [Features](#features)
* [Technology Stack](#technology-stack)
* [Repository Structure](#repository-structure)
* [Setup and Quickstart](#setup-and-quickstart)
* [Environment Configuration](#environment-configuration)
* [Database](#database)
* [Seed Demo Data](#seed-demo-data)
* [Running the Application](#running-the-application)
* [Testing and Linting](#testing-and-linting)
* [Test Coverage](#test-coverage)
* [API Reference](#api-reference)
* [API Examples](#api-examples)
* [Core Algorithm](#core-algorithm)
* [Step-by-Step Worked Example](#step-by-step-worked-example)
* [Box Selection Rules](#box-selection-rules)
* [Rejection Reasons](#rejection-reasons)
* [Duplicate SKU Handling](#duplicate-sku-handling)
* [System Assumptions and Units](#system-assumptions-and-units)
* [Error Handling](#error-handling)
* [Known Limitations](#known-limitations)
* [Future Improvements](#future-improvements)
* [OpenAPI Documentation](#openapi-documentation)
* [CI](#ci)
* [AI Usage](#ai-usage)
* [License](#license)

---

# Project Overview

For an ecommerce order containing one or more products, the warehouse needs to determine which shipping box can contain the entire order.

The **Box Selection System** evaluates all active boxes and recommends the cheapest box in which:

1. Every item physically fits.
2. The total contents weight does not exceed the box's maximum weight.
3. The geometric packing algorithm successfully finds a valid arrangement.

If multiple feasible boxes have the same cost, selection is deterministic:

1. Lowest cost.
2. Smaller box volume.
3. Lowest box ID.

If no single active box can contain the complete order, the API returns:

```text
NO_SINGLE_BOX_FITS
```

along with the rejection reason for each evaluated box.

---

# Features

* Django 5.x REST API
* Django REST Framework
* Versioned API under `/api/v1/`
* Product CRUD
* Box CRUD
* Order CRUD with nested order items
* Ad-hoc box recommendation
* Saved-order box recommendation
* Deterministic 3D packing heuristic
* Six possible item orientations
* Exact Decimal arithmetic
* Weight and volume pre-checks
* Individual item dimension pre-check
* Independent placement validation
* Deterministic box selection
* Alternatives and rejected-box explanations
* Configurable maximum number of expanded units
* Django admin
* Demo data management command
* Pytest test suite
* Brute-force cross-check test
* Ruff linting and formatting
* Coverage reporting
* GitHub Actions CI
* OpenAPI / Swagger documentation

---

# Technology Stack

| Technology            | Purpose                                  |
| --------------------- | ---------------------------------------- |
| Python 3.11+          | Programming language                     |
| Django 5.x            | Web framework                            |
| Django REST Framework | REST API                                 |
| SQLite                | Default development database             |
| PostgreSQL            | Supported through database configuration |
| pytest                | Testing                                  |
| pytest-django         | Django integration for pytest            |
| coverage              | Test coverage                            |
| Ruff                  | Linting and formatting                   |
| drf-spectacular       | OpenAPI documentation                    |

The core packing algorithm does **not** use a third-party bin-packing library such as `py3dbp`.

The packing implementation is contained in:

```text
boxes/services/packing.py
```

and does not import Django or the ORM.

---

# Repository Structure

```text
boxwise/
│
├── manage.py
├── requirements.txt
├── pyproject.toml
├── .gitignore
├── .env.example
├── README.md
├── AI_USAGE.md
├── TEST_OUTPUT.md
│
├── .github/
│   └── workflows/
│       └── ci.yml
│
├── config/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
└── boxes/
    ├── __init__.py
    ├── admin.py
    ├── apps.py
    ├── exceptions.py
    ├── models.py
    ├── serializers.py
    ├── urls.py
    ├── views.py
    │
    ├── services/
    │   ├── __init__.py
    │   ├── packing.py
    │   └── selection.py
    │
    ├── management/
    │   └── commands/
    │       └── seed_demo_data.py
    │
    ├── migrations/
    │
    └── tests/
        ├── test_api.py
        ├── test_brute_force.py
        ├── test_commands.py
        ├── test_models.py
        ├── test_packing.py
        └── test_selection.py
```

---

# Setup and Quickstart

## 1. Clone the repository

```bash
git clone <repository-url>
cd boxwise
```

---

## 2. Create a virtual environment

### Windows PowerShell

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### Linux/macOS

```bash
python -m venv venv
source venv/bin/activate
```

---

## 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

---

## 4. Apply migrations

```bash
python manage.py migrate
```

---

## 5. Seed demo data

```bash
python manage.py seed_demo_data --clear
```

The `--clear` option clears existing demo records before loading the sample data.

---

## 6. Run the development server

```bash
python manage.py runserver
```

The API will be available at:

```text
http://127.0.0.1:8000/
```

Swagger UI:

```text
http://127.0.0.1:8000/api/schema/swagger-ui/
```

Admin panel:

```text
http://127.0.0.1:8000/admin/
```

---

# Environment Configuration

Create a `.env` file from `.env.example` when environment-specific configuration is required.

Example:

```env
SECRET_KEY=your-development-secret-key
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
DATABASE_URL=
MAX_ORDER_UNITS=200
```

For local development, safe defaults are provided.

The database configuration supports SQLite by default and can be configured for PostgreSQL using `DATABASE_URL`.

Do not commit real secrets or production credentials to Git.

---

# Database

SQLite is used by default for easy local development.

Run migrations with:

```bash
python manage.py migrate
```

The main database entities are:

## Product

Stores product information:

* SKU
* name
* length
* width
* height
* weight
* active status
* timestamps

Dimensions and weight must be greater than zero.

## Box

Stores:

* name
* internal length
* internal width
* internal height
* maximum contents weight
* cost
* optional empty weight
* active status
* timestamps

Box dimensions and maximum weight must be greater than zero.

Box cost may be zero or greater.

## Order

Stores an order reference and creation timestamp.

## OrderItem

Associates products with an order and stores the requested quantity.

The same product can occur only once per saved order.

## BoxRecommendation

Stores an audit record containing:

* order
* recommended box
* result status
* recommendation payload
* creation timestamp

---

# Seed Demo Data

The project includes:

```bash
python manage.py seed_demo_data
```

To clear existing demo records first:

```bash
python manage.py seed_demo_data --clear
```

This command creates realistic products, boxes, and sample orders for local development and testing.

---

# Running the Application

Start the server:

```bash
python manage.py runserver
```

Then open:

```text
http://127.0.0.1:8000/
```

Swagger documentation:

```text
http://127.0.0.1:8000/api/schema/swagger-ui/
```

---

# Testing and Linting

## Django system check

```bash
python manage.py check
```

Expected result:

```text
System check identified no issues (0 silenced).
```

---

## Run the full test suite

```bash
pytest
```

The project test suite covers:

* API behavior
* model constraints
* packing pre-checks
* rotations
* exact-fit boundaries
* geometry failures
* deterministic packing
* selection rules
* alternatives
* rejected boxes
* no-single-box cases
* performance for large quantities
* brute-force cross-checking
* seed data command

---

## Run Ruff

```bash
ruff check .
```

---

## Check formatting

```bash
ruff format --check .
```

---

## Automatically format files

```bash
ruff format .
```

---

# Test Coverage

Run:

```bash
coverage run -m pytest
coverage report
```

The project targets more than 90% coverage for the core packing and selection modules.

The verified coverage for the current implementation is:

```text
boxes/services/packing.py       92.57%
boxes/services/selection.py    100.00%
TOTAL                           95.21%
```

The coverage requirement is particularly important for the packing and selection modules because these contain the core decision-making logic.

---

# API Reference

All REST endpoints are versioned under:

```text
/api/v1/
```

## Products

### List products

```http
GET /api/v1/products/
```

Optional filtering:

```http
GET /api/v1/products/?is_active=true
```

### Create product

```http
POST /api/v1/products/
```

Example:

```json
{
  "sku": "PROD-BOOK",
  "name": "Hardcover Book",
  "length": "24.00",
  "width": "17.00",
  "height": "3.50",
  "weight": "0.850",
  "is_active": true
}
```

---

# Boxes

### List boxes

```http
GET /api/v1/boxes/
```

Optional filtering:

```http
GET /api/v1/boxes/?is_active=true
```

### Create box

```http
POST /api/v1/boxes/
```

Example:

```json
{
  "name": "Small Shipping Box",
  "internal_length": "25.00",
  "internal_width": "20.00",
  "internal_height": "15.00",
  "max_weight": "5.00",
  "cost": "1.20",
  "empty_weight": "0.20",
  "is_active": true
}
```

---

# Orders

### List orders

```http
GET /api/v1/orders/
```

### Create order

Orders accept nested items.

```http
POST /api/v1/orders/
```

Example:

```json
{
  "reference": "ORDER-1001",
  "items": [
    {
      "sku": "PROD-BOOK",
      "quantity": 2
    },
    {
      "sku": "PROD-MUG",
      "quantity": 1
    }
  ]
}
```

---

# Ad-Hoc Box Recommendation

An ad-hoc recommendation does not create an order.

```http
POST /api/v1/recommend-box/
```

Request:

```json
{
  "items": [
    {
      "sku": "PROD-BOOK",
      "quantity": 2
    },
    {
      "sku": "PROD-MUG",
      "quantity": 1
    }
  ]
}
```

---

# Saved Order Recommendation

```http
GET /api/v1/orders/{id}/recommend-box/
```

This evaluates the products belonging to the saved order.

A recommendation can also create an audit record through `BoxRecommendation`.

---

# API Response

A successful recommendation has the following general structure:

```json
{
  "status": "RECOMMENDED",
  "recommended_box": {
    "id": 3,
    "name": "Medium Shipping Box",
    "cost": "2.10",
    "dimensions": [
      "35.00",
      "28.00",
      "20.00"
    ]
  },
  "order_summary": {
    "total_items": 3,
    "total_weight": "2.150",
    "total_volume": "4056.00"
  },
  "utilisation": {
    "volume_pct": 20.6,
    "weight_pct": 10.8
  },
  "placements": [],
  "alternatives": [],
  "rejected_boxes": []
}
```

The exact placement list contains the position and oriented dimensions for every expanded item.

---

# API Example

## Request

```bash
curl -X POST http://127.0.0.1:8000/api/v1/recommend-box/ \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {
        "sku": "PROD-BOOK",
        "quantity": 2
      },
      {
        "sku": "PROD-MUG",
        "quantity": 1
      }
    ]
  }'
```

---

# Core Algorithm

The packing engine is implemented in:

```text
boxes/services/packing.py
```

It is deliberately independent of Django and the ORM.

The algorithm is a deterministic heuristic for 3D bin packing.

Exact 3D bin packing is NP-hard, so this implementation does not attempt to find a mathematically optimal packing arrangement for every possible input.

Instead, it guarantees:

* deterministic behavior
* valid geometry for every successful packing
* no overlapping placements
* no placement outside the box
* exact Decimal comparisons
* documented rejection reasons

The heuristic can produce **false negatives**, but it must never produce a false positive.

---

# Algorithm Steps

## 1. Expand order quantities

An order line such as:

```text
PROD-BOOK × 3
```

is expanded into three individual items:

```text
PROD-BOOK#1
PROD-BOOK#2
PROD-BOOK#3
```

This simplifies geometric placement.

---

## 2. Sort items deterministically

Items are processed using deterministic ordering based on:

1. Volume descending
2. Longest dimension descending
3. Stable item identifier

This means the same input produces the same packing result.

---

## 3. Pre-check every box

Before running geometric packing, each active box is checked for obvious failures.

### Weight

If:

```text
total item weight > box max_weight
```

the box is rejected:

```text
WEIGHT_EXCEEDED
```

### Volume

If:

```text
total item volume > box volume
```

the box is rejected:

```text
VOLUME_EXCEEDED
```

### Individual item dimensions

The dimensions of an item and box are sorted independently.

For example:

```text
Item:
10 × 20 × 30

Box:
15 × 25 × 30
```

Sorted comparison:

```text
10 <= 15
20 <= 25
30 <= 30
```

Therefore the item can fit in at least one orientation.

This test is only an individual-item pre-check. It does not prove that the complete order fits.

If an individual item cannot fit in any orientation:

```text
ITEM_TOO_LARGE
```

---

# Extreme Points Packing

For boxes that pass the pre-checks, the system uses an Extreme Points placement heuristic.

The initial candidate point is:

```text
(0, 0, 0)
```

After placing an item, new candidate points are generated around its boundaries.

Candidates are evaluated deterministically using:

```text
z ASC
y ASC
x ASC
```

For every item, the algorithm tries each unique allowed orientation at each candidate position.

---

# Placement Validation

A placement is valid only if:

```text
x >= 0
y >= 0
z >= 0
```

and:

```text
x + item_length <= box_length
y + item_width  <= box_width
z + item_height <= box_height
```

The algorithm also checks pairwise overlap.

Two items that only touch at a face are allowed.

For example:

```text
Item A ends at x = 10
Item B starts at x = 10
```

is valid.

Actual intersection is not allowed.

Before returning a successful packing, the independent:

```text
validate_placements()
```

function re-checks:

* bounds
* pairwise overlap

This provides the zero-false-positive guarantee.

---

# Box Selection Rules

After evaluating every active box:

### Feasible boxes

Feasible boxes are sorted by:

```text
cost ASC
volume ASC
id ASC
```

Therefore:

1. Cheapest box wins.
2. If costs are equal, smaller volume wins.
3. If cost and volume are equal, lower ID wins.

The first feasible box is:

```text
recommended_box
```

The next two feasible boxes are:

```text
alternatives
```

Every rejected box is included with its machine-readable reason.

---

# Step-by-Step Worked Example

Consider an order containing:

```text
2 × Hardcover Book
Dimensions: 24 × 17 × 3.5 cm
Weight: 0.85 kg each

1 × Coffee Mug
Dimensions: 12 × 10 × 10 cm
Weight: 0.45 kg
```

Total quantity:

```text
3 items
```

Total weight:

```text
(2 × 0.85) + 0.45
= 2.15 kg
```

Total volume:

```text
2 × (24 × 17 × 3.5)
+ (12 × 10 × 10)

= 2856 + 1200
= 4056 cm³
```

---

## Candidate Box

Consider:

```text
Medium Shipping Box

Dimensions:
35 × 28 × 20 cm

Maximum contents weight:
10 kg

Cost:
2.10
```

### Step 1 — Weight

```text
Order weight = 2.15 kg
Box capacity = 10 kg

2.15 <= 10
```

Pass.

### Step 2 — Volume

Box volume:

```text
35 × 28 × 20
= 19600 cm³
```

Order volume:

```text
4056 cm³
```

Therefore:

```text
4056 <= 19600
```

Pass.

### Step 3 — Individual dimensions

All three items can fit individually within:

```text
35 × 28 × 20
```

Pass.

### Step 4 — Placement

The deterministic packing algorithm tries orientations and candidate points.

One valid arrangement is:

```text
Book 1:
position = (0, 0, 0)
dimensions = (24, 17, 3.5)

Book 2:
position = (0, 0, 3.5)
dimensions = (24, 17, 3.5)

Mug:
position = (24, 0, 0)
dimensions = (10, 12, 10)
```

The mug is rotated from:

```text
12 × 10 × 10
```

to:

```text
10 × 12 × 10
```

The mug occupies the remaining area beside the books.

The validator then checks the complete placement.

If all bounds and pairwise overlap checks pass, the box is considered feasible.

---

# Rejection Reasons

The system uses machine-readable rejection reasons.

| Reason             | Meaning                                                                      |
| ------------------ | ---------------------------------------------------------------------------- |
| `WEIGHT_EXCEEDED`  | Total order weight exceeds box maximum contents weight                       |
| `ITEM_TOO_LARGE`   | At least one item cannot fit in any orientation                              |
| `VOLUME_EXCEEDED`  | Total item volume exceeds box volume                                         |
| `NO_PACKING_FOUND` | Pre-checks pass, but the heuristic cannot find a valid geometric arrangement |

A box can pass the volume check but still fail geometrically.

For example, two objects may have a combined volume smaller than the box while their shapes prevent them from being arranged inside it.

---

# Duplicate SKU Handling

Duplicate SKUs in a recommendation request are **merged by summing their quantities**.

For example:

```json
{
  "items": [
    {
      "sku": "PROD-BOOK",
      "quantity": 2
    },
    {
      "sku": "PROD-BOOK",
      "quantity": 3
    }
  ]
}
```

is treated as:

```json
{
  "items": [
    {
      "sku": "PROD-BOOK",
      "quantity": 5
    }
  ]
}
```

This behavior prevents duplicate request lines from producing inconsistent packing input.

---

# System Assumptions and Units

## Dimensions

All dimensions are measured in:

```text
centimetres (cm)
```

---

## Weight

Weights are measured in:

```text
kilograms (kg)
```

---

## Cost

Cost is represented as a Decimal value in a single application currency.

The system does not perform currency conversion.

---

## Box Dimensions

Box dimensions represent the **internal usable dimensions** of the box.

External cardboard thickness is not considered.

---

## Weight Limit

`max_weight` represents the maximum weight of the **contents**.

The optional `empty_weight` field is stored for reference but is ignored by the recommendation weight check by default.

Therefore:

```text
contents weight <= max_weight
```

is the relevant condition.

---

## Rotation

Products can be rotated into any of their six possible 3D orientations unless a future orientation restriction is introduced.

For dimensions:

```text
L × W × H
```

the algorithm considers permutations of these dimensions.

Duplicate orientations, such as those produced by equal dimensions, are not unnecessarily repeated.

---

## Decimal Precision

Money, dimensions, and weights use Python/Django `Decimal` values.

The algorithm avoids floating-point arithmetic for geometric and financial comparisons.

This prevents precision problems such as:

```text
0.1 + 0.2 != 0.3
```

when represented using binary floating-point arithmetic.

---

## Padding and Void Fill

Protective packaging such as:

* bubble wrap
* paper
* foam
* air pillows

is outside the scope of this implementation.

---

# API Validation and Errors

The API uses consistent validation responses.

Examples of invalid input include:

* empty item list
* zero quantity
* negative quantity
* unknown SKU
* inactive product
* excessive expanded unit count
* invalid product/box dimensions

Unknown saved orders return:

```text
404 Not Found
```

Invalid request data returns:

```text
400 Bad Request
```

The API does not intentionally return a 500 response for normal client validation errors.

---

# Maximum Order Size

The system limits the number of expanded individual units processed by the packing algorithm.

The default limit is:

```text
200 units
```

For example:

```text
500 × PROD-SMALL
```

will be rejected rather than attempting to pack 500 units.

This protects the application from unexpectedly expensive geometric calculations.

The limit can be configured through application settings/environment configuration.

---

# Known Limitations

## 1. Heuristic false negatives

3D bin packing is computationally difficult.

The Extreme Points heuristic may fail to find a packing even if another more sophisticated arrangement exists.

Therefore:

```text
NO_PACKING_FOUND
```

does not necessarily prove mathematical impossibility.

However, a successful result is independently validated and must have valid geometry.

---

## 2. No exact optimization

The algorithm does not search every possible arrangement.

It prioritizes:

* deterministic behavior
* explainability
* reasonable performance
* correctness of successful placements

over guaranteed globally optimal packing.

---

## 3. No fragile-item rules

The current implementation does not enforce rules such as:

```text
THIS SIDE UP
FRAGILE
DO NOT STACK
```

---

## 4. No stacking-weight restrictions

The algorithm does not currently model product-specific stacking limits.

---

## 5. No padding or void-fill calculations

The available internal dimensions are treated as fully usable space.

---

## 6. Single-box recommendation

The primary recommendation system attempts to find **one box** that can contain the complete order.

If no single box works, it returns:

```text
NO_SINGLE_BOX_FITS
```

A multi-box splitting algorithm is not part of the current production recommendation flow.

---

# Future Improvements

## 1. Multi-box splitting

Implement a First-Fit-Decreasing based multi-box fallback for orders that cannot fit inside one box.

The feature would be treated as heuristic/experimental because minimizing total packaging cost across multiple boxes introduces another optimization problem.

---

## 2. Fragility and stacking rules

Add product-level constraints such as:

```text
allow_rotation
fragile
max_stack_weight
this_side_up
```

---

## 3. Caching

Recommendation results could be cached based on a normalized SKU/quantity payload.

This could reduce repeated calculations for identical orders.

---

## 4. Async Processing

Very large order batches could be processed asynchronously using background workers such as Celery.

The current implementation deliberately limits expanded units to avoid unbounded synchronous processing.

---

# OpenAPI Documentation

The project uses `drf-spectacular` for OpenAPI documentation.

After starting the server, Swagger UI is available at:

```text
http://127.0.0.1:8000/api/schema/swagger-ui/
```

The generated OpenAPI schema can also be accessed through the project's schema endpoint.

---

# Django Admin

The following models are registered in Django admin:

* Product
* Box
* Order
* OrderItem
* BoxRecommendation

The admin provides useful:

* list displays
* filtering
* searching
* relationship visibility

Create a superuser with:

```bash
python manage.py createsuperuser
```

Then visit:

```text
http://127.0.0.1:8000/admin/
```

---

# CI

GitHub Actions runs automated checks on push and pull requests.

The CI workflow performs:

1. Python environment setup
2. Dependency installation
3. Ruff linting
4. Test execution
5. Coverage reporting

Workflow file:

```text
.github/workflows/ci.yml
```

---

# Test Output

The repository contains:

```text
TEST_OUTPUT.md
```

This file should contain the actual locally executed test output.

Test results should never be manually fabricated.

---

# AI Usage

The repository contains:

```text
AI_USAGE.md
```

This file intentionally contains the required section headings for documenting AI assistance.

The final content describing tools, prompts, accepted/rejected output, mistakes, and verification should be completed by the developer.

---

# Development Philosophy

The project intentionally favors:

* readable code
* explicit data structures
* deterministic algorithms
* Decimal arithmetic
* independent validation
* meaningful tests
* simple Django architecture
* explainability over clever abstractions

The core packing logic is kept separate from Django so that it can be unit-tested without database or framework dependencies.

---

# License

This project was created as a technical hiring assignment.

Add an appropriate license here if the project is later intended for public distribution.
