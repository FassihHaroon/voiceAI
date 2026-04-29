"""
Agent service — the AI adapter layer.

Responsibilities:
  1. build_menu_context()   → Markdown string for the system prompt (fetched once at session start).
  2. resolve_item()         → Fuzzy-match dish + modifiers → validate required options → store in cart.
  3. remove_item()          → Remove a cart item by cart_item_id.
  4. clear_cart()           → Wipe an entire session cart.
  5. submit_order()         → Consume session cart → call order_service.create_order().

Session cart:
  An in-memory dict keyed by session_id is sufficient for a kiosk with 1-2 concurrent sessions.
  Each value is a list of _CartEntry dicts (internal — never serialised to the AI).

Fuzzy matching:
  Uses difflib.get_close_matches for dish name resolution (handles typos, partial names,
  Roman Urdu transliterations like "pulao" matching "Chicken Pulao").
  For modifiers (piece type, packaging, drink brand) it also uses difflib against the
  dish_sub_options.name values returned from DB.
"""
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from decimal import Decimal
from difflib import get_close_matches
from typing import Optional

from fastapi import HTTPException
from supabase import Client

from .order_service import create_order
from ..schemas.orders import (
    OrderCreateRequest,
    OrderItemIn,
    SelectedOptionIn,
    OrderTypeEnum,
    PaymentMethodEnum,
)
from ..schemas.agent import (
    ResolveItemRequest,
    ResolveItemResponse,
    SubmitOrderRequest,
    SubmitOrderResponse,
    CartItemView,
    CartResponse,
)

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────
# In-memory session store
# ─────────────────────────────────────────────────────────────

@dataclass
class _ResolvedSelection:
    option_id: int
    option_name: str
    sub_option_id: int
    sub_option_name: str
    price: float


@dataclass
class _CartEntry:
    cart_item_id: str
    dish_id: int
    dish_name: str
    quantity: int
    unit_price: float
    selections: list[_ResolvedSelection]
    summary: str
    notes: Optional[str] = None


# session_id → list[_CartEntry]
_sessions: dict[str, list[_CartEntry]] = {}


def _get_session(session_id: str) -> list[_CartEntry]:
    return _sessions.setdefault(session_id, [])


# ─────────────────────────────────────────────────────────────
# Fuzzy helpers
# ─────────────────────────────────────────────────────────────

def _normalise(text: str) -> str:
    """Lowercase, strip punctuation for robust matching."""
    return text.lower().replace("-", " ").replace("_", " ").strip()


def _best_match(query: str, candidates: list[str], cutoff: float = 0.45) -> Optional[str]:
    """Return the closest candidate or None."""
    nq = _normalise(query)
    norm_map = {_normalise(c): c for c in candidates}
    # Try exact normalised match first
    if nq in norm_map:
        return norm_map[nq]
    # Try substring match
    for norm, original in norm_map.items():
        if nq in norm or norm in nq:
            return original
    # Fuzzy fallback
    hits = get_close_matches(nq, list(norm_map.keys()), n=1, cutoff=cutoff)
    if hits:
        return norm_map[hits[0]]
    return None


# ─────────────────────────────────────────────────────────────
# 1. Menu context builder — called once at session start
# ─────────────────────────────────────────────────────────────

def build_menu_context(db: Client) -> str:
    """
    Returns the entire active+available menu as a compact Markdown string
    suitable for injection into the Gemini system prompt.

    Includes all required/optional modifier groups with their choices and prices.
    The AI reads this once and never needs to call a menu-search endpoint during
    an active voice session.
    """
    try:
        # Fetch categories ordered by priority
        cats = db.table("categories").select("id, name, priority").eq("status", 1) \
            .order("priority", desc=True).execute().data

        # Fetch all sub-categories
        subs_data = db.table("sub_categories").select("id, category_id, name").eq("status", 1).execute().data
        subs_by_cat: dict[int, list[dict]] = {}
        for s in subs_data:
            subs_by_cat.setdefault(s["category_id"], []).append(s)

        # Fetch all active+available dishes
        dishes_data = db.table("dishes").select(
            "id, category_id, sub_category_id, name, description, price, base_price, tag"
        ).eq("status", 1).eq("availability", 1).execute().data
        dishes_by_sub: dict[int, list[dict]] = {}
        for d in dishes_data:
            dishes_by_sub.setdefault(d["sub_category_id"], []).append(d)

        # Fetch all dish_options for active dishes
        dish_ids = [d["id"] for d in dishes_data]
        if not dish_ids:
            return "Menu is currently empty."

        options_data = db.table("dish_options").select(
            "id, dish_id, name, required, multiselect, min_select, max_select"
        ).in_("dish_id", dish_ids).execute().data
        options_by_dish: dict[int, list[dict]] = {}
        for o in options_data:
            options_by_dish.setdefault(o["dish_id"], []).append(o)

        # Fetch all sub-options
        opt_ids = [o["id"] for o in options_data]
        sub_opts_by_option: dict[int, list[dict]] = {}
        if opt_ids:
            sub_opts_data = db.table("dish_sub_options").select(
                "id, option_id, name, price"
            ).in_("option_id", opt_ids).execute().data
            for so in sub_opts_data:
                sub_opts_by_option.setdefault(so["option_id"], []).append(so)

        # ── Assemble Markdown ─────────────────────────────────
        lines: list[str] = ["# SAVOUR FOODS MENU\n"]
        lines.append(
            "IMPORTANT: Drink options at Savour Foods are local brands — "
            "Cola Next (cola/coke), Fizzup (lemon/sprite). "
            "Mineral water is 'Savour Mineral Water'. "
            "Do NOT say Pepsi or Coke — say Cola Next.\n"
        )

        for cat in cats:
            cat_subs = subs_by_cat.get(cat["id"], [])
            cat_dishes: list[dict] = []
            for sub in cat_subs:
                cat_dishes.extend(dishes_by_sub.get(sub["id"], []))
            if not cat_dishes:
                continue

            lines.append(f"\n## {cat['name'].upper()}")

            for dish in cat_dishes:
                display_price = float(dish["price"]) if float(dish["price"]) > 0 else float(dish["base_price"])
                price_str = f"Rs{display_price:.0f}" if display_price > 0 else "see variants"
                tag_str = f" [{dish['tag']}]" if dish.get("tag") else ""
                lines.append(f"\n### {dish['name']}{tag_str} — {price_str}")

                if dish.get("description"):
                    lines.append(f"  {dish['description']}")

                dish_opts = options_by_dish.get(dish["id"], [])
                for opt in dish_opts:
                    req_label = "REQUIRED" if opt["required"] else "optional"
                    multi_label = " (choose multiple)" if opt["multiselect"] else ""
                    sub_opts = sub_opts_by_option.get(opt["id"], [])

                    choices: list[str] = []
                    for so in sub_opts:
                        p = float(so["price"])
                        if p > 0:
                            choices.append(f"{so['name']} (Rs{p:.0f})")
                        else:
                            choices.append(so["name"])

                    choices_str = ", ".join(choices) if choices else "—"
                    lines.append(
                        f"  - [{req_label}]{multi_label} {opt['name']}: {choices_str}"
                    )

        return "\n".join(lines)

    except Exception as exc:
        logger.exception("build_menu_context failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ─────────────────────────────────────────────────────────────
# 2. Resolve item — core AI tool handler
# ─────────────────────────────────────────────────────────────

def resolve_item(req: ResolveItemRequest, db: Client) -> ResolveItemResponse:
    """
    Fuzzy-matches the dish and modifiers, validates required option groups,
    stores a resolved cart entry in the session, and returns a summary to the AI.

    On missing required selections → returns status="requires_input" with
    an ai_instruction the LLM can speak directly to the customer.
    """
    try:
        # ── 1. Find the dish ─────────────────────────────────
        dishes_resp = db.table("dishes").select(
            "id, name, price, base_price, status, availability"
        ).eq("status", 1).eq("availability", 1).execute()
        all_dishes = dishes_resp.data or []

        dish_names = [d["name"] for d in all_dishes]
        matched_name = _best_match(req.dish_query, dish_names, cutoff=0.4)

        if not matched_name:
            return ResolveItemResponse(
                status="not_found",
                ai_instruction=(
                    f"I couldn't find '{req.dish_query}' on the menu. "
                    "Ask the customer to clarify what they would like to order."
                ),
            )

        dish = next(d for d in all_dishes if d["name"] == matched_name)

        if dish["status"] != 1 or dish["availability"] != 1:
            return ResolveItemResponse(
                status="not_found",
                ai_instruction=f"'{dish['name']}' is currently not available. Ask the customer to choose something else.",
            )

        # ── 2. Fetch option groups + sub-options ─────────────
        opts_resp = db.table("dish_options").select(
            "id, name, required, multiselect"
        ).eq("dish_id", dish["id"]).execute()
        option_groups = opts_resp.data or []

        if not option_groups:
            # Simple dish — no customisation needed
            unit_price = _dish_base_price(dish)
            entry = _build_cart_entry(dish, unit_price, [], req)
            _get_session(req.session_id).append(entry)
            return ResolveItemResponse(
                status="ok",
                cart_item_id=entry.cart_item_id,
                summary=entry.summary,
                unit_price=entry.unit_price,
            )

        # Load sub-options for all option groups
        opt_ids = [o["id"] for o in option_groups]
        sub_opts_resp = db.table("dish_sub_options").select(
            "id, option_id, name, price"
        ).in_("option_id", opt_ids).execute()
        all_sub_opts = sub_opts_resp.data or []

        sub_opts_by_opt: dict[int, list[dict]] = {}
        for so in all_sub_opts:
            sub_opts_by_opt.setdefault(so["option_id"], []).append(so)

        # ── 3. Match modifiers to sub-options ────────────────
        #   We try to greedily assign each modifier string to an option group.
        #   Priority: required groups first, then optional.

        resolved_selections: list[_ResolvedSelection] = []
        # Track which option groups have been satisfied
        satisfied_opt_ids: set[int] = set()

        for mod_text in req.modifiers:
            for opt in option_groups:
                if opt["id"] in satisfied_opt_ids and not opt["multiselect"]:
                    continue
                sub_opts = sub_opts_by_opt.get(opt["id"], [])
                so_names = [so["name"] for so in sub_opts]
                matched_so_name = _best_match(mod_text, so_names, cutoff=0.4)
                if matched_so_name:
                    so = next(s for s in sub_opts if s["name"] == matched_so_name)
                    resolved_selections.append(_ResolvedSelection(
                        option_id=opt["id"],
                        option_name=opt["name"],
                        sub_option_id=so["id"],
                        sub_option_name=so["name"],
                        price=float(so["price"]),
                    ))
                    satisfied_opt_ids.add(opt["id"])
                    break  # modifier consumed

        # ── 4. Check required groups ─────────────────────────
        required_groups = [o for o in option_groups if o["required"]]
        missing_groups = [
            o for o in required_groups if o["id"] not in satisfied_opt_ids
        ]

        if missing_groups:
            missing_descriptions: list[str] = []
            for mg in missing_groups:
                sub_opts = sub_opts_by_opt.get(mg["id"], [])
                choices = [so["name"] for so in sub_opts]
                choices_str = ", ".join(choices) if choices else "an option"
                missing_descriptions.append(f"{mg['name']} (choose: {choices_str})")

            ai_instruction = (
                f"The order for '{dish['name']}' is incomplete. "
                f"You still need to ask the customer for: "
                + "; ".join(missing_descriptions) + "."
            )
            return ResolveItemResponse(
                status="requires_input",
                ai_instruction=ai_instruction,
            )

        # ── 5. Resolve unit price ─────────────────────────────
        base = Decimal(str(dish["price"]))
        if base == 0:
            # Variant model — price comes from a priced sub-option
            variant_price = next(
                (Decimal(str(s.price)) for s in resolved_selections if s.price > 0),
                None,
            )
            if variant_price is None:
                # edge case: required group existed but all sub-options were free
                variant_price = Decimal(str(dish["base_price"]))
            unit_price = float(variant_price)
        else:
            # Fixed price + any add-on charges
            add_ons = sum(
                Decimal(str(s.price)) for s in resolved_selections if s.price > 0
            )
            unit_price = float(base + add_ons)

        # ── 6. Build cart entry and store ────────────────────
        entry = _build_cart_entry(dish, unit_price, resolved_selections, req)
        _get_session(req.session_id).append(entry)

        logger.info(
            "resolve_item OK — session=%s dish=%s cart_item=%s price=%.2f",
            req.session_id, dish["name"], entry.cart_item_id, unit_price,
        )

        return ResolveItemResponse(
            status="ok",
            cart_item_id=entry.cart_item_id,
            summary=entry.summary,
            unit_price=entry.unit_price,
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("resolve_item failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ─────────────────────────────────────────────────────────────
# 3. Remove item
# ─────────────────────────────────────────────────────────────

def remove_item(session_id: str, cart_item_id: str) -> dict:
    cart = _get_session(session_id)
    original_len = len(cart)
    _sessions[session_id] = [e for e in cart if e.cart_item_id != cart_item_id]
    if len(_sessions[session_id]) == original_len:
        raise HTTPException(status_code=404, detail=f"cart_item_id '{cart_item_id}' not found in session")
    return {"removed": cart_item_id}


# ─────────────────────────────────────────────────────────────
# 4. Clear cart
# ─────────────────────────────────────────────────────────────

def clear_cart(session_id: str) -> dict:
    _sessions[session_id] = []
    return {"cleared": True, "session_id": session_id}


# ─────────────────────────────────────────────────────────────
# 5. Get cart view
# ─────────────────────────────────────────────────────────────

def get_cart(session_id: str) -> CartResponse:
    cart = _get_session(session_id)
    items = [
        CartItemView(
            cart_item_id=e.cart_item_id,
            summary=e.summary,
            quantity=e.quantity,
            unit_price=e.unit_price,
            item_total=round(e.unit_price * e.quantity, 2),
        )
        for e in cart
    ]
    subtotal = round(sum(i.item_total for i in items), 2)
    return CartResponse(session_id=session_id, items=items, subtotal=subtotal)


# ─────────────────────────────────────────────────────────────
# 6. Submit order
# ─────────────────────────────────────────────────────────────

def submit_order(req: SubmitOrderRequest, db: Client) -> SubmitOrderResponse:
    """
    Reads the in-memory session cart, converts each entry to an OrderItemIn,
    and calls the existing order_service.create_order to persist to Supabase.
    """
    cart = _get_session(req.session_id)

    if not cart:
        raise HTTPException(status_code=400, detail="Cart is empty. Nothing to submit.")

    order_items: list[OrderItemIn] = []
    for entry in cart:
        selected_options = [
            SelectedOptionIn(
                option_id=sel.option_id,
                sub_option_id=sel.sub_option_id,
            )
            for sel in entry.selections
        ]
        order_items.append(OrderItemIn(
            dish_id=entry.dish_id,
            quantity=entry.quantity,
            selected_options=selected_options,
            notes=entry.notes,
        ))

    order_request = OrderCreateRequest(
        customer_name=req.customer_name,
        customer_phone=req.customer_phone,
        customer_address=req.customer_address,
        order_type=req.order_type,
        payment_method=req.payment_method,
        notes=req.notes,
        items=order_items,
    )

    try:
        created = create_order(order_request, db)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("submit_order → create_order failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    # Clear session on success
    _sessions[req.session_id] = []

    total = float(created["total_amount"])
    summary = (
        f"Order confirmed! Order ID: {created['id']}. "
        f"Total: Rs{total:,.0f}. Thank you!"
    )

    logger.info("submit_order OK — order_id=%s total=%.2f", created["id"], total)

    return SubmitOrderResponse(
        order_id=created["id"],
        total_amount=total,
        summary=summary,
    )


# ─────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────

def _dish_base_price(dish: dict) -> float:
    p = float(dish["price"])
    return p if p > 0 else float(dish["base_price"])


def _build_cart_entry(
    dish: dict,
    unit_price: float,
    selections: list[_ResolvedSelection],
    req: ResolveItemRequest,
) -> _CartEntry:
    """Build a _CartEntry with a human-readable summary."""
    mods_str = ""
    if selections:
        parts = [s.sub_option_name for s in selections]
        mods_str = f" ({', '.join(parts)})"

    item_total = round(unit_price * req.quantity, 2)
    summary = (
        f"{dish['name']}{mods_str} × {req.quantity} — Rs{item_total:,.0f}"
    )

    return _CartEntry(
        cart_item_id=str(uuid.uuid4()),
        dish_id=dish["id"],
        dish_name=dish["name"],
        quantity=req.quantity,
        unit_price=unit_price,
        selections=selections,
        summary=summary,
        notes=req.notes,
    )
