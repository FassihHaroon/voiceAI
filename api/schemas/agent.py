"""
Pydantic schemas for the AI-agent adapter layer.

All IDs exposed to the LLM are opaque UUIDs (cart_item_id, session_id).
Integer dish/option/sub-option IDs never leave the server.
"""
from __future__ import annotations
from typing import Literal, Optional
from pydantic import BaseModel, Field

from .orders import OrderTypeEnum, PaymentMethodEnum


# ─────────────────────────────────────────────────────────────
# Inbound — resolve a single item the AI heard
# ─────────────────────────────────────────────────────────────

class ResolveItemRequest(BaseModel):
    session_id: str = Field(..., description="Opaque voice-session identifier (generated client-side per call)")
    dish_query: str = Field(..., description="Dish name as the customer said it (free text, will be fuzzy-matched)")
    modifiers: list[str] = Field(
        default_factory=list,
        description="Customisation choices as free-text strings, e.g. ['leg piece', 'boxed', 'no sauce']",
    )
    quantity: int = Field(default=1, ge=1, description="Number of units")
    notes: Optional[str] = Field(default=None, description="Special instructions for this item")


# ─────────────────────────────────────────────────────────────
# Outbound — result of resolving an item
# ─────────────────────────────────────────────────────────────

class ResolveItemResponse(BaseModel):
    status: Literal["ok", "requires_input", "not_found"]
    # Set when status == "ok"
    cart_item_id: Optional[str] = None
    summary: Optional[str] = Field(
        default=None,
        description="Human-readable confirmation string the AI can read back to the customer",
    )
    unit_price: Optional[float] = None
    # Set when status != "ok"
    ai_instruction: Optional[str] = Field(
        default=None,
        description="Plain-English instruction telling the AI what to ask the customer next",
    )


# ─────────────────────────────────────────────────────────────
# Inbound — remove a single item from the in-flight cart
# ─────────────────────────────────────────────────────────────

class RemoveItemRequest(BaseModel):
    session_id: str
    cart_item_id: str = Field(..., description="cart_item_id returned by a previous resolve-item call")


# ─────────────────────────────────────────────────────────────
# Inbound — clear the whole cart for a session
# ─────────────────────────────────────────────────────────────

class ClearCartRequest(BaseModel):
    session_id: str


# ─────────────────────────────────────────────────────────────
# Inbound — submit the finalised order
# ─────────────────────────────────────────────────────────────

class SubmitOrderRequest(BaseModel):
    session_id: str
    customer_name: str = Field(..., min_length=1, max_length=150)
    customer_phone: str = Field(..., min_length=1, max_length=20)
    customer_address: Optional[str] = Field(default=None, description="Required for delivery orders")
    order_type: OrderTypeEnum = OrderTypeEnum.dine_in
    payment_method: PaymentMethodEnum = PaymentMethodEnum.cash
    notes: Optional[str] = None


# ─────────────────────────────────────────────────────────────
# Outbound — submit result
# ─────────────────────────────────────────────────────────────

class SubmitOrderResponse(BaseModel):
    order_id: str
    total_amount: float
    summary: str   # e.g. "Order #xyz confirmed. Total Rs 1,540."


# ─────────────────────────────────────────────────────────────
# Outbound — current cart view (nice to have for debugging)
# ─────────────────────────────────────────────────────────────

class CartItemView(BaseModel):
    cart_item_id: str
    summary: str
    quantity: int
    unit_price: float
    item_total: float


class CartResponse(BaseModel):
    session_id: str
    items: list[CartItemView]
    subtotal: float
