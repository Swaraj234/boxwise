from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Box, BoxRecommendation, Order, Product
from .serializers import (
    AdHocRecommendBoxRequestSerializer,
    BoxSerializer,
    OrderSerializer,
    ProductSerializer,
)
from .services.packing import BoxSpec, Item
from .services.selection import SelectionResult, select_box


def _format_recommendation_response(sel: SelectionResult) -> dict:
    rec_box_data = None
    if sel.recommended_box:
        rec_box_data = {
            "id": sel.recommended_box.box_id,
            "name": sel.recommended_box.name,
            "cost": f"{sel.recommended_box.cost:.2f}",
            "dimensions": [
                f"{sel.recommended_box.internal_length:.2f}",
                f"{sel.recommended_box.internal_width:.2f}",
                f"{sel.recommended_box.internal_height:.2f}",
            ],
        }

    placements_data = [
        {
            "item_id": p.item_id,
            "sku": p.sku,
            "position": [f"{p.x:.2f}", f"{p.y:.2f}", f"{p.z:.2f}"],
            "dimensions": [f"{p.dim_x:.2f}", f"{p.dim_y:.2f}", f"{p.dim_z:.2f}"],
        }
        for p in sel.placements
    ]

    alternatives_data = [
        {
            "id": alt.box.box_id,
            "name": alt.box.name,
            "cost": f"{alt.box.cost:.2f}",
            "dimensions": [
                f"{alt.box.internal_length:.2f}",
                f"{alt.box.internal_width:.2f}",
                f"{alt.box.internal_height:.2f}",
            ],
        }
        for alt in sel.alternatives
    ]

    rejected_data = [
        {
            "id": rej.id,
            "name": rej.name,
            "reason": rej.reason,
            "detail": rej.detail,
        }
        for rej in sel.rejected_boxes
    ]

    return {
        "status": sel.status,
        "recommended_box": rec_box_data,
        "order_summary": {
            "total_items": sel.order_summary.total_items,
            "total_weight": f"{sel.order_summary.total_weight:.3f}",
            "total_volume": f"{sel.order_summary.total_volume:.2f}",
        },
        "utilisation": sel.utilisation,
        "placements": placements_data,
        "alternatives": alternatives_data,
        "rejected_boxes": rejected_data,
    }


def _expand_and_run_selection(
    items_sku_qty: list[dict],
) -> tuple[dict, Box | None, SelectionResult]:
    # Expand line items into unit Item objects
    expanded_items: list[Item] = []
    unit_id_counter = 1

    for line in items_sku_qty:
        sku = line["sku"]
        qty = line["quantity"]
        product = Product.objects.get(sku=sku)

        for _ in range(qty):
            expanded_items.append(
                Item(
                    item_id=unit_id_counter,
                    sku=product.sku,
                    length=product.length,
                    width=product.width,
                    height=product.height,
                    weight=product.weight,
                )
            )
            unit_id_counter += 1

    # Fetch active boxes
    active_boxes_db = Box.objects.filter(is_active=True).order_by("cost", "name")
    box_specs = [
        BoxSpec(
            box_id=b.id,
            name=b.name,
            internal_length=b.internal_length,
            internal_width=b.internal_width,
            internal_height=b.internal_height,
            max_weight=b.max_weight,
            cost=b.cost,
        )
        for b in active_boxes_db
    ]

    selection_res = select_box(expanded_items, box_specs)
    response_payload = _format_recommendation_response(selection_res)

    db_rec_box = None
    if selection_res.recommended_box:
        db_rec_box = Box.objects.get(id=selection_res.recommended_box.box_id)

    return response_payload, db_rec_box, selection_res


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    search_fields = ["sku", "name"]
    filterset_fields = ["is_active"]

    def get_queryset(self):
        qs = super().get_queryset()
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            val = is_active.lower() in ("true", "1")
            qs = qs.filter(is_active=val)
        return qs


class BoxViewSet(viewsets.ModelViewSet):
    queryset = Box.objects.all()
    serializer_class = BoxSerializer
    search_fields = ["name"]
    filterset_fields = ["is_active"]

    def get_queryset(self):
        qs = super().get_queryset()
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            val = is_active.lower() in ("true", "1")
            qs = qs.filter(is_active=val)
        return qs


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    @extend_schema(responses={200: dict})
    @action(detail=True, methods=["get"], url_path="recommend-box")
    def recommend_box(self, request, pk=None):
        order = self.get_object()
        order_items = order.items.all().select_related("product")

        if not order_items.exists():
            return Response(
                {
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Order contains no items.",
                        "details": {},
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        items_sku_qty = []
        for oi in order_items:
            if not oi.product.is_active:
                return Response(
                    {
                        "error": {
                            "code": "VALIDATION_ERROR",
                            "message": f"Product with SKU '{oi.product.sku}' is inactive.",
                            "details": {},
                        }
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            items_sku_qty.append({"sku": oi.product.sku, "quantity": oi.quantity})

        response_payload, rec_box, selection_res = _expand_and_run_selection(items_sku_qty)

        # Audit recommendation
        BoxRecommendation.objects.create(
            order=order,
            recommended_box=rec_box,
            result_status=selection_res.status,
            payload=response_payload,
        )

        return Response(response_payload, status=status.HTTP_200_OK)


class AdHocRecommendBoxView(APIView):
    @extend_schema(
        request=AdHocRecommendBoxRequestSerializer,
        responses={200: dict},
    )
    def post(self, request):
        serializer = AdHocRecommendBoxRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        items_sku_qty = serializer.validated_data["items"]
        response_payload, _, _ = _expand_and_run_selection(items_sku_qty)

        return Response(response_payload, status=status.HTTP_200_OK)
