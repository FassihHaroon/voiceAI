"""
Pydantic schemas for all menu-related API responses.
Mirrors the DB tables: categories, sub_categories, dishes,
dish_options, dish_sub_options.
"""
from __future__ import annotations
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, computed_field


# ─────────────────────────────────────────────────────────────
# Sub-option  (innermost leaf)
# ─────────────────────────────────────────────────────────────

class DishSubOptionResponse(BaseModel):
    id: int
    option_id: int
    dish_id: int
    name: str
    price: Decimal
    priority: int


# ─────────────────────────────────────────────────────────────
# Option group  (e.g. "Packaging", "Choose Your Piece")
# ─────────────────────────────────────────────────────────────

class DishOptionResponse(BaseModel):
    id: int
    dish_id: int
    name: str
    required: int        # 1 = customer must choose
    multiselect: int     # 1 = can pick multiple sub-options
    min_select: int
    max_select: int
    priority: int
    dish_sub_options: list[DishSubOptionResponse] = []


# ─────────────────────────────────────────────────────────────
# Dish — lightweight (no nested options)
# ─────────────────────────────────────────────────────────────

class DishSummaryResponse(BaseModel):
    """Used in list/menu endpoints — no nested options to keep payload small."""
    id: int
    category_id: int
    sub_category_id: int
    name: str
    description: Optional[str] = None
    price: Decimal
    base_price: Decimal
    tag: Optional[str] = None
    status: int
    availability: int

    @computed_field
    @property
    def display_price(self) -> Decimal:
        """Convenience: the price the UI should show (shelf price or base price)."""
        return self.price if self.price > 0 else self.base_price


# ─────────────────────────────────────────────────────────────
# Dish — full detail with nested options
# ─────────────────────────────────────────────────────────────

class DishDetailResponse(DishSummaryResponse):
    """Used in single-dish endpoint — includes all option groups and choices."""
    dish_options: list[DishOptionResponse] = []


# ─────────────────────────────────────────────────────────────
# Sub-category
# ─────────────────────────────────────────────────────────────

class SubCategoryResponse(BaseModel):
    id: int
    category_id: int
    name: str
    status: int
    dishes: list[DishSummaryResponse] = []


# ─────────────────────────────────────────────────────────────
# Category  (top level)
# ─────────────────────────────────────────────────────────────

class CategoryResponse(BaseModel):
    id: int
    name: str
    status: int
    priority: int


class CategoryWithSubsResponse(CategoryResponse):
    """Category including its sub-categories (no dishes nested here)."""
    sub_categories: list[SubCategoryResponse] = []


# ─────────────────────────────────────────────────────────────
# Full hierarchical menu response
# ─────────────────────────────────────────────────────────────

class FullMenuCategoryResponse(BaseModel):
    """One category block in the full menu response."""
    id: int
    name: str
    priority: int
    sub_categories: list[SubCategoryWithDishesResponse] = []


class SubCategoryWithDishesResponse(BaseModel):
    id: int
    name: str
    dishes: list[DishSummaryResponse] = []


# Resolve forward references
FullMenuCategoryResponse.model_rebuild()
