"""
Order service — all business logic for creating and managing orders.

Key responsibilities:
  1. Validate that each requested dish is active and available.
  2. Resolve the unit price for each dish (fixed vs. variant-price model).
  3. Validate that all REQUIRED option groups have a selection.
  4. Snapshot selected options as JSONB (history-safe even if menu later changes).
  5. Compute subtotal / total_amount.
  6. Bulk-insert order_items in one call.
  7. Enforce the 7-state order status machine.

Pricing rules (per schema comments):
  - dish.price > 0  → base unit price; selected sub-options with price > 0 are ADD-ONS.
  - dish.price == 0 → price MUST come from the chosen priced sub-option (variant model).
"""
from __future__ import annotations
import logging
from decimal import Decimal
from typing import Optional
from fastapi import HTTPException
from supabase import Client

from ..schemas.orders import (
    OrderCreateRequest,
    OrderStatusEnum,
    PaymentStatusEnum,
)

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
# Status state machine
# ─────────────────────────────────────────────────────────────

_STATUS_TRANSITIONS: dict[str, list[str]] = {
    "pending":          ["confirmed", "cancelled"],
    "confirmed":        ["preparing", "cancelled"],
    "preparing":        ["ready", "cancelled"],
    "ready":            ["out_for_delivery", "delivered", "cancelled"],
    "out_for_delivery": ["delivered", "cancelled"],
    "delivered":        [],
    "cancelled":        [],
}


# ─────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────

def _fetch_dish(dish_id: int, db: Client) -> dict:
    resp = db.table("dishes").select(
        "id, name, price, base_price, status, availability"
    ).eq("id", dish_id).execute()
    if not resp.data:
        raise HTTPException(status_code=404, detail=f"Dish {dish_id} not found")
    dish = resp.data[0]
    if dish["status"] != 1 or dish["availability"] != 1:
        raise HTTPException(
            status_code=400,
            detail=f"Dish '{dish['name']}' (id={dish_id}) is currently unavailable",
        )
    return dish


def _fetch_option(option_id: int, db: Client) -> dict:
    resp = db.table("dish_options").select(
        "id, dish_id, name, required"
    ).eq("id", option_id).execute()
    if not resp.data:
        raise HTTPException(
            status_code=404, detail=f"Option group {option_id} not found"
        )
    return resp.data[0]


def _fetch_sub_option(sub_option_id: int, option_id: int, db: Client) -> dict:
    resp = db.table("dish_sub_options").select(
        "id, option_id, dish_id, name, price"
    ).eq("id", sub_option_id).eq("option_id", option_id).execute()
    if not resp.data:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Sub-option {sub_option_id} not found "
                f"or does not belong to option group {option_id}"
            ),
        )
    return resp.data[0]


def _fetch_required_options(dish_id: int, db: Client) -> list[int]:
    """Return ids of all REQUIRED option groups for a dish."""
    resp = db.table("dish_options").select("id").eq("dish_id", dish_id).eq("required", 1).execute()
    return [r["id"] for r in (resp.data or [])]


def _resolve_price_and_snapshot(
    dish: dict,
    selected_options: list,   # list[SelectedOptionIn]
    db: Client,
) -> tuple[Decimal, list[dict]]:
    """
    Returns (unit_price, snapshot_list).

    snapshot_list elements:
      {option_id, option_name, sub_option_id, choice_name, extra_price}

    Pricing logic:
      - dish.price > 0  → start with dish.price; priced sub-options are add-ons.
      - dish.price == 0 → unit_price comes from the first priced sub-option selected
                          (variant model — customer must pick a priced variant).
    """
    dish_price = Decimal(str(dish["price"]))
    snapshot: list[dict] = []
    add_ons = Decimal("0")
    variant_price: Optional[Decimal] = None

    # Validate required option groups are covered
    required_ids = set(_fetch_required_options(dish["id"], db))
    selected_option_ids = {sel.option_id for sel in selected_options}
    missing = required_ids - selected_option_ids
    if missing:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Dish '{dish['name']}' has required option group(s) "
                f"with id(s) {list(missing)} that must be selected"
            ),
        )

    for sel in selected_options:
        opt = _fetch_option(sel.option_id, db)
        # Ensure the option belongs to this dish
        if opt["dish_id"] != dish["id"]:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Option group {sel.option_id} does not belong to "
                    f"dish {dish['id']}"
                ),
            )
        sub = _fetch_sub_option(sel.sub_option_id, sel.option_id, db)
        sub_price = Decimal(str(sub["price"]))

        snapshot.append({
            "option_id":    opt["id"],
            "option_name":  opt["name"],
            "sub_option_id": sub["id"],
            "choice_name":  sub["name"],
            "extra_price":  float(sub_price),
        })

        if sub_price > 0:
            if dish_price == 0:
                # First priced sub-option IS the variant price
                if variant_price is None:
                    variant_price = sub_price
            else:
                # Fixed-price dish: positive sub-option = add-on charge
                add_ons += sub_price

    if dish_price == 0:
        if variant_price is None:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Dish '{dish['name']}' requires a priced variant selection "
                    f"(dish.price is 0 — a sub-option with price > 0 must be chosen)"
                ),
            )
        unit_price = variant_price
    else:
        unit_price = dish_price + add_ons

    return unit_price, snapshot


# ─────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────

def create_order(order_in: OrderCreateRequest, db: Client) -> dict:
    """
    Full order creation flow:
      1. Validate all dishes (active + available).
      2. Validate required option groups.
      3. Resolve unit prices + build JSONB snapshots.
      4. Compute subtotal and total_amount.
      5. Insert order row.
      6. Bulk-insert all order_items in ONE call.
      7. Return full order with items.
    """
    try:
        resolved_items: list[dict] = []
        subtotal = Decimal("0")

        for item in order_in.items:
            dish = _fetch_dish(item.dish_id, db)
            unit_price, snapshot = _resolve_price_and_snapshot(
                dish, item.selected_options, db
            )
            item_subtotal = unit_price * item.quantity
            subtotal += item_subtotal

            resolved_items.append({
                "dish_id":         dish["id"],
                "dish_name":       dish["name"],
                "quantity":        item.quantity,
                "unit_price":      float(unit_price),
                "selected_options": snapshot,
                "notes":           item.notes,
            })

        delivery_fee  = Decimal(str(order_in.delivery_fee))
        discount      = Decimal(str(order_in.discount))
        total_amount  = subtotal + delivery_fee - discount
        if total_amount < 0:
            total_amount = Decimal("0")

        # ── Insert order ──────────────────────────────────────
        order_row = {
            "customer_name":    order_in.customer_name,
            "customer_phone":   order_in.customer_phone,
            "customer_address": order_in.customer_address,
            "order_type":       order_in.order_type.value,
            "payment_method":   order_in.payment_method.value,
            "delivery_fee":     float(delivery_fee),
            "discount":         float(discount),
            "subtotal":         float(subtotal),
            "total_amount":     float(total_amount),
            "notes":            order_in.notes,
            "status":           "pending",
            "payment_status":   "unpaid",
        }
        order_resp = db.table("orders").insert(order_row).execute()
        new_order = order_resp.data[0]
        order_id = new_order["id"]

        # ── Bulk-insert order_items ───────────────────────────
        for li in resolved_items:
            li["order_id"] = order_id
        db.table("order_items").insert(resolved_items).execute()

        # ── Return full order with items ──────────────────────
        return _get_order_with_items(order_id, db)

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("create_order failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


def get_orders(
    db: Client,
    status: Optional[str] = None,
    phone: Optional[str] = None,
    page: int = 1,
    per_page: int = 20,
) -> dict:
    """
    Paginated order list (without embedded items for performance).
    Items are loaded lazily per-order via GET /orders/{id}.
    """
    try:
        offset = (page - 1) * per_page
        q = (
            db.table("orders")
            .select(
                "id, customer_name, customer_phone, customer_address, "
                "order_type, status, payment_method, payment_status, "
                "subtotal, delivery_fee, discount, total_amount, "
                "notes, created_at, updated_at",
                count="exact",
            )
            .order("created_at", desc=True)
            .range(offset, offset + per_page - 1)
        )
        if status:
            q = q.eq("status", status)
        if phone:
            q = q.eq("customer_phone", phone)

        resp = q.execute()
        orders = resp.data or []

        # Attach items to each order in the page
        for order in orders:
            items_resp = (
                db.table("order_items")
                .select("id, order_id, dish_id, dish_name, quantity, unit_price, item_total, selected_options, notes")
                .eq("order_id", order["id"])
                .execute()
            )
            order["items"] = items_resp.data or []

        total = resp.count if resp.count is not None else len(orders)
        return {"total": total, "page": page, "per_page": per_page, "items": orders}

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("get_orders failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


def get_order(order_id: str, db: Client) -> dict:
    """Single order with all items."""
    try:
        return _get_order_with_items(order_id, db)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("get_order failed for order_id=%s", order_id)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


def update_order_status(order_id: str, new_status: OrderStatusEnum, db: Client) -> dict:
    """
    Advance order through the state machine.
    Raises 400 if the transition is not allowed.
    """
    try:
        resp = (
            db.table("orders")
            .select("id, status")
            .eq("id", order_id)
            .execute()
        )
        if not resp.data:
            raise HTTPException(status_code=404, detail=f"Order {order_id} not found")

        current = resp.data[0]["status"]
        target  = new_status.value

        if target == current:
            raise HTTPException(status_code=400, detail=f"Order is already '{current}'")

        allowed = _STATUS_TRANSITIONS.get(current, [])
        if target not in allowed:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Cannot transition from '{current}' to '{target}'. "
                    f"Allowed transitions: {allowed or ['none']}"
                ),
            )

        db.table("orders").update({"status": target}).eq("id", order_id).execute()
        return _get_order_with_items(order_id, db)

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("update_order_status failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


def update_payment_status(
    order_id: str, payment_status: PaymentStatusEnum, db: Client
) -> dict:
    try:
        resp = db.table("orders").select("id").eq("id", order_id).execute()
        if not resp.data:
            raise HTTPException(status_code=404, detail=f"Order {order_id} not found")

        db.table("orders").update(
            {"payment_status": payment_status.value}
        ).eq("id", order_id).execute()
        return _get_order_with_items(order_id, db)

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("update_payment_status failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


def delete_order(order_id: str, db: Client) -> dict:
    """Hard-delete an order (CASCADE removes order_items)."""
    try:
        resp = db.table("orders").select("id").eq("id", order_id).execute()
        if not resp.data:
            raise HTTPException(status_code=404, detail=f"Order {order_id} not found")

        db.table("orders").delete().eq("id", order_id).execute()
        return {"message": f"Order {order_id} and all its items have been deleted"}

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("delete_order failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ─────────────────────────────────────────────────────────────
# Private helper
# ─────────────────────────────────────────────────────────────

def _get_order_with_items(order_id: str, db: Client) -> dict:
    """Fetch order row + all its items in two queries."""
    order_resp = (
        db.table("orders")
        .select(
            "id, customer_name, customer_phone, customer_address, "
            "order_type, status, payment_method, payment_status, "
            "subtotal, delivery_fee, discount, total_amount, "
            "notes, created_at, updated_at"
        )
        .eq("id", order_id)
        .execute()
    )
    if not order_resp.data:
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found")

    order = order_resp.data[0]
    items_resp = (
        db.table("order_items")
        .select(
            "id, order_id, dish_id, dish_name, quantity, "
            "unit_price, item_total, selected_options, notes"
        )
        .eq("order_id", order_id)
        .execute()
    )
    order["items"] = items_resp.data or []
    return order
