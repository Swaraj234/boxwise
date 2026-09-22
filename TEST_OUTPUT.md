# Test Output Log

## Environment

```text
platform win32 -- Python 3.13.2
pytest 8.3.3
Django 5.1.1
pytest-django 4.9.0
```

## Django System Check

```text
> python manage.py check
System check identified no issues (0 silenced).
```

## Pytest

Command:

```text
pytest
```

Result:

```text
============================================================= test session starts ==============================================================
platform win32 -- Python 3.13.2, pytest-8.3.3, pluggy-1.6.0 -- C:\Users\offic\OneDrive\Desktop\boxwise\venv\Scripts\python.exe
cachedir: .pytest_cache
django: version: 5.1.1, settings: config.settings (from ini)
rootdir: C:\Users\offic\OneDrive\Desktop\boxwise
configfile: pyproject.toml
plugins: django-4.9.0
collected 44 items

boxes/tests/test_api.py::TestProductAPI::test_list_products PASSED
boxes/tests/test_api.py::TestProductAPI::test_filter_active_products PASSED
boxes/tests/test_api.py::TestProductAPI::test_create_product PASSED
boxes/tests/test_api.py::TestBoxAPI::test_list_boxes PASSED
boxes/tests/test_api.py::TestOrderAPI::test_create_order_with_items PASSED
boxes/tests/test_api.py::TestOrderAPI::test_get_order_recommendation PASSED
boxes/tests/test_api.py::TestAdHocRecommendationAPI::test_ad_hoc_recommendation_happy_path PASSED
boxes/tests/test_api.py::TestAdHocRecommendationAPI::test_merge_duplicate_skus PASSED
boxes/tests/test_api.py::TestAdHocRecommendationAPI::test_inactive_product_in_request_returns_400 PASSED
boxes/tests/test_api.py::TestAdHocRecommendationAPI::test_unknown_sku_returns_400 PASSED
boxes/tests/test_api.py::TestAdHocRecommendationAPI::test_empty_items_returns_400 PASSED
boxes/tests/test_api.py::TestAdHocRecommendationAPI::test_negative_quantity_returns_400 PASSED
boxes/tests/test_api.py::TestAdHocRecommendationAPI::test_filter_inactive_products PASSED
boxes/tests/test_api.py::TestAdHocRecommendationAPI::test_filter_inactive_boxes PASSED
boxes/tests/test_api.py::TestAdHocRecommendationAPI::test_empty_order_recommendation_returns_400 PASSED
boxes/tests/test_api.py::TestAdHocRecommendationAPI::test_exceeding_max_200_units_returns_400 PASSED
boxes/tests/test_api.py::TestAdHocRecommendationAPI::test_order_not_found_returns_404 PASSED
boxes/tests/test_commands.py::test_seed_demo_data_command PASSED
boxes/tests/test_models.py::TestProductModel::test_create_valid_product PASSED
boxes/tests/test_models.py::TestProductModel::test_product_dimension_check_constraint PASSED
boxes/tests/test_models.py::TestProductModel::test_product_weight_check_constraint PASSED
boxes/tests/test_models.py::TestBoxModel::test_create_valid_box PASSED
boxes/tests/test_models.py::TestBoxModel::test_box_check_constraints PASSED
boxes/tests/test_models.py::TestOrderAndItems::test_create_order_with_items PASSED
boxes/tests/test_models.py::TestOrderAndItems::test_order_item_unique_together PASSED
boxes/tests/test_models.py::TestBoxRecommendationModel::test_create_box_recommendation PASSED
boxes/tests/test_brute_force.py::TestBruteForceCrossCheck::test_brute_force_cross_check PASSED
boxes/tests/test_packing.py::TestPackingPreChecks::test_weight_exceeded PASSED
boxes/tests/test_packing.py::TestPackingPreChecks::test_volume_exceeded PASSED
boxes/tests/test_packing.py::TestPackingPreChecks::test_item_too_large PASSED
boxes/tests/test_packing.py::TestBoundariesAndRotations::test_exact_fit_dimensions PASSED
boxes/tests/test_packing.py::TestBoundariesAndRotations::test_item_point_01_cm_too_large PASSED
boxes/tests/test_packing.py::TestBoundariesAndRotations::test_weight_exact_and_over PASSED
boxes/tests/test_packing.py::TestBoundariesAndRotations::test_item_fits_only_when_rotated PASSED
boxes/tests/test_packing.py::TestGeometryNoFitAndDeterminism::test_volume_fits_geometry_fails PASSED
boxes/tests/test_packing.py::TestGeometryNoFitAndDeterminism::test_determinism_under_shuffled_input PASSED
boxes/tests/test_packing.py::TestGeometryNoFitAndDeterminism::test_identical_items_ascending_item_id_order PASSED
boxes/tests/test_packing.py::TestPerformance::test_pack_200_small_items_under_time_limit PASSED
boxes/tests/test_selection.py::TestSelectionEngine::test_cheapest_box_wins_over_smaller_expensive_box PASSED
boxes/tests/test_selection.py::TestSelectionEngine::test_tie_break_smaller_volume PASSED
boxes/tests/test_selection.py::TestSelectionEngine::test_tie_break_lowest_id PASSED
boxes/tests/test_selection.py::TestSelectionEngine::test_tie_break_lowest_numeric_id_10_vs_2 PASSED
boxes/tests/test_selection.py::TestSelectionEngine::test_alternatives_and_rejected_boxes_formatting PASSED
boxes/tests/test_selection.py::TestSelectionEngine::test_no_single_box_fits PASSED

============================================================== 44 passed in 1.38s ==============================================================
```

## Coverage

Command:

```text
coverage run -m pytest
coverage report
```

Test result:

```text
============================================================== 44 passed in 2.10s ==============================================================
```

Coverage report:

```text
Name                                          Stmts   Miss   Cover   Missing
----------------------------------------------------------------------------
boxes\__init__.py                                 0      0 100.00%
boxes\admin.py                                   37      1  97.30%   56
boxes\apps.py                                     4      0 100.00%
boxes\exceptions.py                              28      6  78.57%   23, 25, 47, 49-51
boxes\management\__init__.py                      0      0 100.00%
boxes\management\commands\__init__.py             0      0 100.00%
boxes\management\commands\seed_demo_data.py      43      0 100.00%
boxes\models.py                                  69      1  98.55%   136
boxes\serializers.py                             91      7  92.31%   54, 77, 82, 97-99, 127
boxes\services\packing.py                       148     11  92.57%   85, 87, 89, 91, 104, 165, 179, 223-224, 227, 312
boxes\services\selection.py                      51      0 100.00%
boxes\urls.py                                     8      0 100.00%
boxes\views.py                                   85      1  98.82%   186
----------------------------------------------------------------------------
TOTAL                                           564     27  95.21%
```

## Ruff

### Lint Check

Command:

```text
ruff check .
```

Result:

```text
All checks passed!
```

### Format Check

Command:

```text
ruff format --check .
```

Result:

```text
26 files already formatted
```

## Final Result

```text
Django system check: PASS
Tests: 44 passed, 0 failed
Packing coverage: 92.57%
Selection coverage: 100.00%
Overall coverage: 95.21%
Ruff linting: PASS
Ruff formatting: PASS
Warnings: None
```
