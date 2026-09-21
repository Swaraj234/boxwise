# Test Output Log

```text
============================= test session starts =============================
platform win32 -- Python 3.13.2, pytest-8.3.3, pluggy-1.6.0
django: version: 5.1.1, settings: config.settings (from ini)
rootdir: C:\Users\offic\OneDrive\Desktop\boxwise
configfile: pyproject.toml
plugins: anyio-4.9.0, django-4.9.0
collected 42 items

boxes/tests/test_api.py::TestProductAPI::test_list_products PASSED       [  2%]
boxes/tests/test_api.py::TestProductAPI::test_filter_active_products PASSED [  4%]
boxes/tests/test_api.py::TestProductAPI::test_create_product PASSED      [  7%]
boxes/tests/test_api.py::TestBoxAPI::test_list_boxes PASSED              [  9%]
boxes/tests/test_api.py::TestOrderAPI::test_create_order_with_items PASSED [ 11%]
boxes/tests/test_api.py::TestOrderAPI::test_get_order_recommendation PASSED [ 14%]
boxes/tests/test_api.py::TestAdHocRecommendationAPI::test_ad_hoc_recommendation_happy_path PASSED [ 16%]
boxes/tests/test_api.py::TestAdHocRecommendationAPI::test_merge_duplicate_skus PASSED [ 19%]
boxes/tests/test_api.py::TestAdHocRecommendationAPI::test_inactive_product_in_request_returns_400 PASSED [ 21%]
boxes/tests/test_api.py::TestAdHocRecommendationAPI::test_unknown_sku_returns_400 PASSED [ 23%]
boxes/tests/test_api.py::TestAdHocRecommendationAPI::test_empty_items_returns_400 PASSED [ 26%]
boxes/tests/test_api.py::TestAdHocRecommendationAPI::test_negative_quantity_returns_400 PASSED [ 28%]
boxes/tests/test_api.py::TestAdHocRecommendationAPI::test_filter_inactive_products PASSED [ 30%]
boxes/tests/test_api.py::TestAdHocRecommendationAPI::test_filter_inactive_boxes PASSED [ 33%]
boxes/tests/test_api.py::TestAdHocRecommendationAPI::test_empty_order_recommendation_returns_400 PASSED [ 35%]
boxes/tests/test_api.py::TestAdHocRecommendationAPI::test_exceeding_max_200_units_returns_400 PASSED [ 38%]
boxes/tests/test_api.py::TestAdHocRecommendationAPI::test_order_not_found_returns_404 PASSED [ 40%]
boxes/tests/test_commands.py::test_seed_demo_data_command PASSED        [ 42%]
boxes/tests/test_models.py::TestProductModel::test_create_valid_product PASSED [ 45%]
boxes/tests/test_models.py::TestProductModel::test_product_dimension_check_constraint PASSED [ 47%]
boxes/tests/test_models.py::TestProductModel::test_product_weight_check_constraint PASSED [ 50%]
boxes/tests/test_models.py::TestBoxModel::test_create_valid_box PASSED   [ 52%]
boxes/tests/test_models.py::TestBoxModel::test_box_check_constraints PASSED [ 54%]
boxes/tests/test_models.py::TestOrderAndItems::test_create_order_with_items PASSED [ 57%]
boxes/tests/test_models.py::TestOrderAndItems::test_order_item_unique_together PASSED [ 59%]
boxes/tests/test_models.py::TestBoxRecommendationModel::test_create_box_recommendation PASSED [ 61%]
boxes/tests/test_brute_force.py::TestBruteForceCrossCheck::test_brute_force_cross_check PASSED [ 64%]
boxes/tests/test_packing.py::TestPackingPreChecks::test_weight_exceeded PASSED [ 66%]
boxes/tests/test_packing.py::TestPackingPreChecks::test_volume_exceeded PASSED [ 69%]
boxes/tests/test_packing.py::TestPackingPreChecks::test_item_too_large PASSED [ 71%]
boxes/tests/test_packing.py::TestBoundariesAndRotations::test_exact_fit_dimensions PASSED [ 73%]
boxes/tests/test_packing.py::TestBoundariesAndRotations::test_item_point_01_cm_too_large PASSED [ 76%]
boxes/tests/test_packing.py::TestBoundariesAndRotations::test_weight_exact_and_over PASSED [ 78%]
boxes/tests/test_packing.py::TestBoundariesAndRotations::test_item_fits_only_when_rotated PASSED [ 80%]
boxes/tests/test_packing.py::TestGeometryNoFitAndDeterminism::test_volume_fits_geometry_fails PASSED [ 83%]
boxes/tests/test_packing.py::TestGeometryNoFitAndDeterminism::test_determinism_under_shuffled_input PASSED [ 85%]
boxes/tests/test_packing.py::TestPerformance::test_pack_200_small_items_under_time_limit PASSED [ 88%]
boxes/tests/test_selection.py::TestSelectionEngine::test_cheapest_box_wins_over_smaller_expensive_box PASSED [ 90%]
boxes/tests/test_selection.py::TestSelectionEngine::test_tie_break_smaller_volume PASSED [ 92%]
boxes/tests/test_selection.py::TestSelectionEngine::test_tie_break_lowest_id PASSED [ 95%]
boxes/tests/test_selection.py::TestSelectionEngine::test_alternatives_and_rejected_boxes_formatting PASSED [ 97%]
boxes/tests/test_selection.py::TestSelectionEngine::test_no_single_box_fits PASSED [100%]

======================= 42 passed, 10 warnings in 2.66s =======================

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
boxes\services\packing.py                       147     10  93.20%   85, 87, 89, 91, 104, 165, 179, 224-225, 228
boxes\services\selection.py                      51      0 100.00%
boxes\urls.py                                     8      0 100.00%
boxes\views.py                                   85      1  98.82%   186
----------------------------------------------------------------------------
TOTAL                                           563     26  95.38%
```
