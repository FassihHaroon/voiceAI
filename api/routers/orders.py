"""
Orders router — full CRUD for orders.
Prefix: /api/v1/orders
"""
from typing import Optional
from fastapi import APIRouter, Query

from ..database import get_db
from ..schemas.orders import (
    OrderCreateRequest,
    OrderResponse,
    OrderStatusUpdateRequest,
    PaymentStatusUpdateRequest,
    PaginatedOrdersResponse,
    OrderStatusEnum,
)
from ..services import order_service

router = APIRouter(prefix="/orders", tags=["Orders"])


# ─────────────────────────────────────────────────────────────
# List orders (paginated)
# ─────────────────────────────────────────────────────────────

@router.get(
    "",
    response_model=PaginatedOrdersResponse,
    summary="List orders (paginated)",
    description=(
        "Returns a paginated list of orders, newest first. "
        "Filter by `status` and/or `phone`. "
        "Each order includes its line items."
    ),
)
def list_orders(
    status:   Optional[OrderStatusEnum] = Query(None, description="Filter by order status"),
    phone:    Optional[str]             = Query(None, description="Filter by customer phone"),
    page:     int                       = Query(1,    ge=1,       description="Page number (1-based)"),
    per_page: int                       = Query(20,   ge=1, le=100, description="Items per page"),
):
    db = get_db()
    return order_service.get_orders(
        db,
        status=status.value if status else None,
        phone=phone,
        page=page,
        per_page=per_page,
    )


# ─────────────────────────────────────────────────────────────
# Create order
# ─────────────────────────────────────────────────────────────

@router.post(
    "",
    response_model=OrderResponse,
    status_code=201,
    summary="Create a new order",
    description="""
Create a new customer order.

**Pricing rules:**
- For dishes with a fixed `price > 0`: unit price = `dish.price` + any add-on sub-option prices.
- For dishes with `price = 0` (variant model): you **must** include a `selected_options` entry
  pointing to the priced sub-option — that sub-option's price becomes the unit price.

**Required options:**
- If a `dish_options` row has `required = 1`, you must include a selection for it in
  `selected_options`, otherwise the request is rejected with HTTP 400.

**Example flow:**
1. `GET /api/v1/menu/dishes/{dish_id}` → see option groups and sub-options.
2. Build `selected_options` list with `option_id` + `sub_option_id` pairs.
3. Submit this endpoint.
""",
)
def create_order(body: OrderCreateRequest):
    db = get_db()
    return order_service.create_order(body, db)


# ─────────────────────────────────────────────────────────────
# Get single order
# ─────────────────────────────────────────────────────────────

@router.get(
    "/{order_id}",
    response_model=OrderResponse,
    summary="Get a single order with all line items",
)
def get_order(order_id: str):
    db = get_db()
    return order_service.get_order(order_id, db)


# ─────────────────────────────────────────────────────────────
# Update order status
# ─────────────────────────────────────────────────────────────

@router.patch(
    "/{order_id}/status",
    response_model=OrderResponse,
    summary="Advance order status",
    description="""
Move an order through the fulfilment pipeline.

**Valid transitions:**
```
pending → confirmed → preparing → ready → out_for_delivery → delivered
   ↓           ↓           ↓        ↓              ↓
cancelled   cancelled  cancelled cancelled      cancelled
```
Attempting an invalid transition returns HTTP 400.
""",
)
def update_status(order_id: str, body: OrderStatusUpdateRequest):
    db = get_db()
    return order_service.update_order_status(order_id, body.status, db)


# ─────────────────────────────────────────────────────────────
# Update payment status
# ─────────────────────────────────────────────────────────────

@router.patch(
    "/{order_id}/payment",
    response_model=OrderResponse,
    summary="Update payment status",
    description="Set payment status to `unpaid`, `paid`, or `refunded`.",
)
def update_payment(order_id: str, body: PaymentStatusUpdateRequest):
    db = get_db()
    return order_service.update_payment_status(order_id, body.payment_status, db)


# ─────────────────────────────────────────────────────────────
# Delete order
# ─────────────────────────────────────────────────────────────

@router.delete(
    "/{order_id}",
    summary="Delete an order",
    description="Hard-deletes the order and all its line items (CASCADE). Use with caution.",
)
def delete_order(order_id: str):
    db = get_db()
    return order_service.delete_order(order_id, db)
