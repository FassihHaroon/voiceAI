"""
Menu service — all database queries related to the menu hierarchy.

Query strategy (avoids N+1):
  - Full menu:   3 queries (categories, sub_categories, dishes) → assembled in Python.
  - Dish detail: 1 query with nested PostgREST select (dish + options + sub-options).
  - Search:      1 query with ilike filter on dishes.name.
"""
from __future__ import annotations
import logging
from typing import Optional
from fastapi import HTTPException
from supabase import Client

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────
# Full hierarchical menu
# ─────────────────────────────────────────────────────────────

def get_full_menu(db: Client) -> list[dict]:
    """
    Returns the full active menu as:
      [ { category, sub_categories: [ { sub_category, dishes: [...] } ] } ]

    Uses 3 flat queries and assembles in Python — avoids N+1 round-trips.
    """
    try:
        # 1. Active categories ordered by priority descending
        cats_resp = (
            db.table("categories")
            .select("id, name, priority, status")
            .eq("status", 1)
            .order("priority", desc=True)
            .execute()
        )
        categories = cats_resp.data

        # 2. All active sub-categories
        subs_resp = (
            db.table("sub_categories")
            .select("id, category_id, name, status")
            .eq("status", 1)
            .execute()
        )
        sub_categories = subs_resp.data

        # 3. All active+available dishes
        dishes_resp = (
            db.table("dishes")
            .select(
                "id, category_id, sub_category_id, name, description, "
                "price, base_price, tag, status, availability"
            )
            .eq("status", 1)
            .eq("availability", 1)
            .execute()
        )
        dishes = dishes_resp.data

        # ── Assemble in Python ──────────────────────────────────
        # Map sub_category_id → list of dishes
        dishes_by_sub: dict[int, list[dict]] = {}
        for d in dishes:
            sid = d["sub_category_id"]
            dishes_by_sub.setdefault(sid, []).append(d)

        # Map category_id → list of sub-categories (with dishes embedded)
        subs_by_cat: dict[int, list[dict]] = {}
        for s in sub_categories:
            cid = s["category_id"]
            s["dishes"] = dishes_by_sub.get(s["id"], [])
            subs_by_cat.setdefault(cid, []).append(s)

        # Build final structure
        result = []
        for cat in categories:
            cat["sub_categories"] = subs_by_cat.get(cat["id"], [])
            result.append(cat)

        logger.debug("get_full_menu: %d categories returned", len(result))
        return result

    except Exception as exc:
        logger.exception("get_full_menu failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ─────────────────────────────────────────────────────────────
# Categories
# ─────────────────────────────────────────────────────────────

def get_categories(db: Client) -> list[dict]:
    try:
        resp = (
            db.table("categories")
            .select("id, name, priority, status")
            .order("priority", desc=True)
            .execute()
        )
        return resp.data
    except Exception as exc:
        logger.exception("get_categories failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


def get_category_by_id(category_id: int, db: Client) -> dict:
    try:
        resp = (
            db.table("categories")
            .select("id, name, priority, status")
            .eq("id", category_id)
            .single()
            .execute()
        )
        if not resp.data:
            raise HTTPException(status_code=404, detail=f"Category {category_id} not found")
        return resp.data
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("get_category_by_id failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


def get_sub_categories(category_id: int, db: Client) -> list[dict]:
    try:
        resp = (
            db.table("sub_categories")
            .select("id, category_id, name, status")
            .eq("category_id", category_id)
            .execute()
        )
        return resp.data
    except Exception as exc:
        logger.exception("get_sub_categories failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ─────────────────────────────────────────────────────────────
# Dishes
# ─────────────────────────────────────────────────────────────

def get_dishes(
    db: Client,
    category_id: Optional[int] = None,
    sub_category_id: Optional[int] = None,
    active_only: bool = True,
) -> list[dict]:
    """Flat dish list — no nested options (fast for listing pages)."""
    try:
        q = db.table("dishes").select(
            "id, category_id, sub_category_id, name, description, "
            "price, base_price, tag, status, availability"
        )
        if active_only:
            q = q.eq("status", 1).eq("availability", 1)
        if category_id is not None:
            q = q.eq("category_id", category_id)
        if sub_category_id is not None:
            q = q.eq("sub_category_id", sub_category_id)
        resp = q.order("name").execute()
        return resp.data
    except Exception as exc:
        logger.exception("get_dishes failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


def get_dish_detail(dish_id: int, db: Client) -> dict:
    """
    Single dish with ALL option groups and sub-options nested.
    Uses PostgREST nested select — single DB round-trip.
    """
    try:
        resp = (
            db.table("dishes")
            .select(
                "id, category_id, sub_category_id, name, description, "
                "price, base_price, tag, status, availability, "
                "dish_options("
                "  id, dish_id, name, required, multiselect, "
                "  min_select, max_select, priority, "
                "  dish_sub_options(id, option_id, dish_id, name, price, priority)"
                ")"
            )
            .eq("id", dish_id)
            .single()
            .execute()
        )
        if not resp.data:
            raise HTTPException(status_code=404, detail=f"Dish {dish_id} not found")

        # Sort option groups and sub-options by priority desc
        dish = resp.data
        dish["dish_options"] = sorted(
            dish.get("dish_options") or [],
            key=lambda o: o.get("priority", 0),
            reverse=True,
        )
        for opt in dish["dish_options"]:
            opt["dish_sub_options"] = sorted(
                opt.get("dish_sub_options") or [],
                key=lambda s: s.get("priority", 0),
                reverse=True,
            )
        return dish
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("get_dish_detail failed for dish_id=%s", dish_id)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


def search_dishes(query: str, db: Client) -> list[dict]:
    """Case-insensitive partial match on dish name."""
    try:
        resp = (
            db.table("dishes")
            .select(
                "id, category_id, sub_category_id, name, description, "
                "price, base_price, tag, status, availability"
            )
            .eq("status", 1)
            .eq("availability", 1)
            .ilike("name", f"%{query}%")
            .order("name")
            .execute()
        )
        return resp.data
    except Exception as exc:
        logger.exception("search_dishes failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


def toggle_dish_availability(dish_id: int, availability: int, db: Client) -> dict:
    """Set availability = 0 or 1 for a dish."""
    if availability not in (0, 1):
        raise HTTPException(status_code=400, detail="availability must be 0 or 1")
    try:
        # Verify exists
        check = db.table("dishes").select("id").eq("id", dish_id).execute()
        if not check.data:
            raise HTTPException(status_code=404, detail=f"Dish {dish_id} not found")

        resp = (
            db.table("dishes")
            .update({"availability": availability})
            .eq("id", dish_id)
            .execute()
        )
        return resp.data[0]
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("toggle_dish_availability failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
