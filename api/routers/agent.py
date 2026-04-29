"""
Agent router — endpoints exclusively for the Gemini voice agent.
Prefix: /api/v1/agent

These are the ONLY endpoints given to the AI as Gemini Tool declarations.
Existing /menu and /orders routes are not touched.
"""
from fastapi import APIRouter
from ..database import get_db
from ..schemas.agent import (
    ResolveItemRequest,
    ResolveItemResponse,
    RemoveItemRequest,
    ClearCartRequest,
    SubmitOrderRequest,
    SubmitOrderResponse,
    CartResponse,
)
from ..services import agent_service

router = APIRouter(prefix="/agent", tags=["Agent"])


# ─────────────────────────────────────────────────────────────
# Menu context  (call once at session start, inject into system prompt)
# ─────────────────────────────────────────────────────────────

@router.get(
    "/menu-context",
    response_model=str,
    summary="Full menu as a compact Markdown string",
    description=(
        "Returns the entire active menu — categories, dishes, required/optional modifiers, "
        "prices and choices — as a single Markdown string. "
        "Inject this into the Gemini system prompt at session start so the AI "
        "knows the full menu without making any tool calls while the customer is speaking."
    ),
)
def get_menu_context() -> str:
    db = get_db()
    return agent_service.build_menu_context(db)


# ─────────────────────────────────────────────────────────────
# Resolve item  (primary AI tool — called every time user orders something)
# ─────────────────────────────────────────────────────────────

@router.post(
    "/resolve-item",
    response_model=ResolveItemResponse,
    summary="Add a dish to the session cart",
    description="""
Fuzzy-matches the dish name and modifier strings, validates all required option groups,
computes the correct unit price, and stores a resolved cart entry.

**Response status values:**
- `ok` — item added successfully. Return `summary` to the customer.
- `requires_input` — required modifiers are missing. Speak `ai_instruction` to the customer then call this endpoint again with the completed modifiers.
- `not_found` — dish not recognised. Speak `ai_instruction` and ask the customer to clarify.
""",
)
def resolve_item(body: ResolveItemRequest) -> ResolveItemResponse:
    db = get_db()
    return agent_service.resolve_item(body, db)


# ─────────────────────────────────────────────────────────────
# Remove item
# ─────────────────────────────────────────────────────────────

@router.post(
    "/remove-item",
    summary="Remove a specific item from the session cart",
    description="Pass the `cart_item_id` returned by a previous `resolve-item` call.",
)
def remove_item(body: RemoveItemRequest) -> dict:
    return agent_service.remove_item(body.session_id, body.cart_item_id)


# ─────────────────────────────────────────────────────────────
# Clear cart
# ─────────────────────────────────────────────────────────────

@router.post(
    "/clear-cart",
    summary="Clear the entire session cart",
    description="Removes all items from the cart for the given session_id.",
)
def clear_cart(body: ClearCartRequest) -> dict:
    return agent_service.clear_cart(body.session_id)


# ─────────────────────────────────────────────────────────────
# View cart  (useful for the frontend UI to display current cart)
# ─────────────────────────────────────────────────────────────

@router.get(
    "/cart/{session_id}",
    response_model=CartResponse,
    summary="View the current cart for a session",
)
def get_cart(session_id: str) -> CartResponse:
    return agent_service.get_cart(session_id)


# ─────────────────────────────────────────────────────────────
# Submit order  (called when the customer confirms)
# ─────────────────────────────────────────────────────────────

@router.post(
    "/submit-order",
    response_model=SubmitOrderResponse,
    status_code=201,
    summary="Finalise and submit the session cart as a real order",
    description="""
Called once the customer confirms their order.

The server reads the in-memory session cart, resolves all dish/option IDs,
and creates a permanent order row in the database via the existing order pipeline.
The session cart is cleared on success.

The AI should only call this **after** explicitly confirming the full order with the customer.
""",
)
def submit_order(body: SubmitOrderRequest) -> SubmitOrderResponse:
    db = get_db()
    return agent_service.submit_order(body, db)
