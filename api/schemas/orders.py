"""
Pydantic schemas for order-related request and response payloads.
Mirrors the DB tables: orders, order_items.
"""
from __future__ import annotations
from decimal import Decimal
from typing import Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


# ─────────────────────────────────────────────────────────────
# Enums matching DB CHECK constraints
# ─────────────────────────────────────────────────────────────

class OrderTypeEnum(str, Enum):
    delivery = "delivery"
    pickup   = "pickup"
    dine_in  = "dine_in"


class OrderStatusEnum(str, Enum):
    pending          = "pending"
    confirmed        = "confirmed"
    preparing        = "preparing"
    ready            = "ready"
    out_for_delivery = "out_for_delivery"
    delivered        = "delivered"
    cancelled        = "cancelled"


class PaymentMethodEnum(str, Enum):
    cash   = "cash"
    card   = "card"
    online = "online"


class PaymentStatusEnum(str, Enum):
    unpaid   = "unpaid"
    paid     = "paid"
    refunded = "refunded"


# ─────────────────────────────────────────────────────────────
# Request — what the client sends when creating an order
# ─────────────────────────────────────────────────────────────

class SelectedOptionIn(BaseModel):
    """A single option/sub-option choice made by the customer."""
    option_id:     int = Field(..., description="ID of the dish_options row")
    sub_option_id: int = Field(..., description="ID of the dish_sub_options row chosen")


class OrderItemIn(BaseModel):
    dish_id:          int   = Field(..., description="dishes.id")
    quantity:         int   = Field(1, ge=1, description="Number of units ordered")
    selected_options: list[SelectedOptionIn] = Field(
        default_factory=list,
        description=(
            "Option choices for this dish. "
            "For dishes with price=0 you MUST include the priced variant sub-option. "
            "For required option groups, include a selection."
        )
    )
    notes: Optional[str] = Field(None, description="Special instructions for this item")


class OrderCreateRequest(BaseModel):
    customer_name:    str            = Field(..., min_length=1, max_length=150)
    customer_phone:   str            = Field(..., min_length=1, max_length=20)
    customer_address: Optional[str]  = Field(None, description="Omit for pickup / dine-in")
    order_type:       OrderTypeEnum  = Field(OrderTypeEnum.delivery)
    payment_method:   PaymentMethodEnum = Field(PaymentMethodEnum.cash)
    delivery_fee:     Decimal        = Field(Decimal("0"), ge=0)
    discount:         Decimal        = Field(Decimal("0"), ge=0)
    instructions:     Optional[str]  = None
    notes:            Optional[str]  = None
    items:            list[OrderItemIn] = Field(..., min_length=1)


# ─────────────────────────────────────────────────────────────
# Request — status / payment updates
# ─────────────────────────────────────────────────────────────

class OrderStatusUpdateRequest(BaseModel):
    status: OrderStatusEnum


class PaymentStatusUpdateRequest(BaseModel):
    payment_status: PaymentStatusEnum


# ─────────────────────────────────────────────────────────────
# Response models
# ─────────────────────────────────────────────────────────────

class OrderItemResponse(BaseModel):
    id:               str
    order_id:         str
    dish_id:          int
    dish_name:        str
    quantity:         int
    unit_price:       Decimal
    item_total:       Decimal
    selected_options: list[Any] = []   # JSONB — returned as-is
    notes:            Optional[str] = None


class OrderResponse(BaseModel):
    id:               str
    customer_name:    str
    customer_phone:   str
    customer_address: Optional[str] = None
    order_type:       str
    status:           str
    payment_method:   str
    payment_status:   str
    subtotal:         Decimal
    delivery_fee:     Decimal
    discount:         Decimal
    total_amount:     Decimal
    instructions:     Optional[str] = None
    notes:            Optional[str] = None
    created_at:       datetime
    updated_at:       datetime
    items:            list[OrderItemResponse] = []


class PaginatedOrdersResponse(BaseModel):
    total:    int
    page:     int
    per_page: int
    items:    list[OrderResponse]
