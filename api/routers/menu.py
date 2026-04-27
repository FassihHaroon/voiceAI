"""
Menu router — all read-only menu endpoints plus the availability toggle.
Prefix: /api/v1/menu
"""
from typing import Optional
from fastapi import APIRouter, Query

from ..database import get_db
from ..schemas.menu import (
    CategoryResponse,
    CategoryWithSubsResponse,
    DishSummaryResponse,
    DishDetailResponse,
    FullMenuCategoryResponse,
)
from ..services import menu_service

router = APIRouter(prefix="/menu", tags=["Menu"])


# ─────────────────────────────────────────────────────────────
# Full menu
# ─────────────────────────────────────────────────────────────

@router.get(
    "",
    response_model=list[FullMenuCategoryResponse],
    summary="Full hierarchical menu",
    description=(
        "Returns all **active** categories ordered by priority, each containing "
        "their sub-categories and active+available dishes. "
        "No option groups — use `GET /menu/dishes/{dish_id}` to fetch options for a specific dish."
    ),
)
def get_full_menu():
    db = get_db()
    return menu_service.get_full_menu(db)


# ─────────────────────────────────────────────────────────────
# Categories
# ─────────────────────────────────────────────────────────────

@router.get(
    "/categories",
    response_model=list[CategoryResponse],
    summary="List all categories",
)
def list_categories():
    db = get_db()
    return menu_service.get_categories(db)


@router.get(
    "/categories/{category_id}",
    response_model=CategoryWithSubsResponse,
    summary="Single category with its sub-categories",
)
def get_category(category_id: int):
    db = get_db()
    cat = menu_service.get_category_by_id(category_id, db)
    cat["sub_categories"] = menu_service.get_sub_categories(category_id, db)
    return cat


# ─────────────────────────────────────────────────────────────
# Dishes
# ─────────────────────────────────────────────────────────────

@router.get(
    "/dishes",
    response_model=list[DishSummaryResponse],
    summary="List all dishes",
    description=(
        "Flat list of active+available dishes. "
        "Filter by `category_id` or `sub_category_id`. "
        "Use `active_only=false` to include inactive/unavailable dishes (admin use)."
    ),
)
def list_dishes(
    category_id:     Optional[int] = Query(None, description="Filter by category ID"),
    sub_category_id: Optional[int] = Query(None, description="Filter by sub-category ID"),
    active_only:     bool          = Query(True,  description="Only return active & available dishes"),
):
    db = get_db()
    return menu_service.get_dishes(
        db,
        category_id=category_id,
        sub_category_id=sub_category_id,
        active_only=active_only,
    )


@router.get(
    "/search",
    response_model=list[DishSummaryResponse],
    summary="Search dishes by name",
    description="Case-insensitive partial match on dish name.",
)
def search_dishes(
    q: str = Query(..., min_length=1, description="Search query"),
):
    db = get_db()
    return menu_service.search_dishes(q, db)


@router.get(
    "/dishes/{dish_id}",
    response_model=DishDetailResponse,
    summary="Single dish with all option groups and sub-options",
    description=(
        "Returns complete dish detail including every option group "
        "(`dish_options`) and every choice (`dish_sub_options`) within each group. "
        "Use this before creating an order to know which selections to send."
    ),
)
def get_dish(dish_id: int):
    db = get_db()
    return menu_service.get_dish_detail(dish_id, db)


@router.patch(
    "/dishes/{dish_id}/availability",
    response_model=DishSummaryResponse,
    summary="Toggle dish availability",
    description="Set `availability` to **1** (available) or **0** (unavailable).",
)
def set_dish_availability(
    dish_id:      int,
    availability: int = Query(..., ge=0, le=1, description="1 = available, 0 = unavailable"),
):
    db = get_db()
    return menu_service.toggle_dish_availability(dish_id, availability, db)
