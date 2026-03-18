import os
from enum import Enum
from fastapi.responses import RedirectResponse
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from supabase import create_client, Client
from dotenv import load_dotenv
from typing import Optional

# Load environment variables
load_dotenv()

# Initialize connection
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

if not url or not key:
    raise ValueError("Supabase URL or Key not found in environment variables.")

supabase: Client = create_client(url, key)

# Initialize FastAPI app
app = FastAPI(
    title="KFC Menu & Orders API",
    description="APIs to manage the KFC menu and customer orders via Supabase",
    version="2.0.0"
)

# ─────────────────────────────────────────────
# Enums (power the Swagger dropdowns)
# ─────────────────────────────────────────────

class CategoryEnum(str, Enum):
    Burgers  = "Burgers"
    Chicken  = "Chicken"
    Sides    = "Sides"
    Drinks   = "Drinks"
    Desserts = "Desserts"

class OrderStatusEnum(str, Enum):
    pending   = "pending"
    confirmed = "confirmed"
    preparing = "preparing"
    ready     = "ready"
    delivered = "delivered"
    cancelled = "cancelled"

# ─────────────────────────────────────────────
# Pydantic models – Menu
# ─────────────────────────────────────────────

class MenuItemCreate(BaseModel):
    name: str
    category: CategoryEnum
    description: Optional[str] = None
    price: float
    available: Optional[bool] = True

class MenuItemUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[CategoryEnum] = None
    description: Optional[str] = None
    price: Optional[float] = None
    available: Optional[bool] = None

class MenuItemResponse(BaseModel):
    id: int
    name: str
    category: str
    description: Optional[str] = None
    price: float
    available: bool

class MenuItemNameResponse(BaseModel):
    id: int
    name: str
    price: float

# ─────────────────────────────────────────────
# Pydantic models – Orders
# ─────────────────────────────────────────────

class OrderItemCreate(BaseModel):
    menu_item_id: int
    quantity: int = 1

class OrderCreate(BaseModel):
    customer_name: str
    items: list[OrderItemCreate]

class OrderUpdate(BaseModel):
    customer_name: Optional[str] = None
    status: Optional[OrderStatusEnum] = None

class OrderItemResponse(BaseModel):
    id: int
    order_id: int
    menu_item_id: int
    quantity: int
    unit_price: float

class OrderResponse(BaseModel):
    id: int
    customer_name: str
    status: str
    total: float
    created_at: str
    items: Optional[list[OrderItemResponse]] = []

# ─────────────────────────────────────────────
# Root redirect
# ─────────────────────────────────────────────

@app.get("/", include_in_schema=False)
def root():
    """Redirect root URL to Swagger docs."""
    return RedirectResponse(url="/docs")

# ─────────────────────────────────────────────
# Menu endpoints
# ─────────────────────────────────────────────

@app.get("/menu/names", response_model=list[MenuItemNameResponse], tags=["Menu"])
def get_menu_names():
    """Get all menu item IDs, names, and prices — use this to pick menu_item_id when creating an order."""
    try:
        response = supabase.table("menu_items").select("id, name, price").order("name").execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/menu", response_model=list[MenuItemResponse], tags=["Menu"])
def get_menu():
    """Fetch all KFC menu items."""
    try:
        response = supabase.table("menu_items").select("*").order("category").execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/menu/category/{category}", response_model=list[MenuItemResponse], tags=["Menu"])
def get_by_category(category: CategoryEnum):
    """Fetch menu items by category — select from the dropdown."""
    try:
        response = supabase.table("menu_items").select("*").eq("category", category.value).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail=f"No items found in category '{category.value}'")
        return response.data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/menu/{item_id}", response_model=list[MenuItemResponse], tags=["Menu"])
def get_menu_item(item_id: int):
    """Fetch a single menu item by ID."""
    try:
        response = supabase.table("menu_items").select("*").eq("id", item_id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Menu item not found")
        return response.data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/menu", response_model=list[MenuItemResponse], status_code=201, tags=["Menu"])
def create_menu_item(item: MenuItemCreate):
    """Add a new item to the KFC menu."""
    try:
        response = supabase.table("menu_items").insert(item.model_dump()).execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/menu/{item_id}", response_model=list[MenuItemResponse], tags=["Menu"])
def update_menu_item(item_id: int, item: MenuItemUpdate):
    """Update an existing menu item by ID."""
    try:
        update_data = {k: v for k, v in item.model_dump().items() if v is not None}
        if not update_data:
            raise HTTPException(status_code=400, detail="No valid fields to update")
        response = supabase.table("menu_items").update(update_data).eq("id", item_id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Menu item not found or no changes made")
        return response.data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/menu/{item_id}", tags=["Menu"])
def delete_menu_item(item_id: int):
    """Delete a menu item by ID."""
    try:
        check = supabase.table("menu_items").select("*").eq("id", item_id).execute()
        if not check.data:
            raise HTTPException(status_code=404, detail="Menu item not found")
        supabase.table("menu_items").delete().eq("id", item_id).execute()
        return {"message": f"Menu item {item_id} successfully deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/menu/{item_id}/availability", response_model=list[MenuItemResponse], tags=["Menu"])
def toggle_availability(item_id: int, available: bool):
    """Toggle the availability of a menu item (mark as in stock / out of stock)."""
    try:
        check = supabase.table("menu_items").select("*").eq("id", item_id).execute()
        if not check.data:
            raise HTTPException(status_code=404, detail="Menu item not found")
        response = supabase.table("menu_items").update({"available": available}).eq("id", item_id).execute()
        return response.data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ─────────────────────────────────────────────
# Orders endpoints
# ─────────────────────────────────────────────

@app.get("/orders", response_model=list[OrderResponse], tags=["Orders"])
def get_orders(
    status: Optional[OrderStatusEnum] = Query(
        default=None,
        description="Filter orders by status — select from the dropdown"
    )
):
    """List all orders. Optionally filter by status using the dropdown."""
    try:
        query = supabase.table("orders").select("*").order("created_at", desc=True)
        if status:
            query = query.eq("status", status.value)
        response = query.execute()
        orders = response.data

        # Attach line items to each order
        for order in orders:
            items_resp = supabase.table("order_items").select("*").eq("order_id", order["id"]).execute()
            order["items"] = items_resp.data

        return orders
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/orders/{order_id}", response_model=OrderResponse, tags=["Orders"])
def get_order(order_id: int):
    """Fetch a single order with all its line items."""
    try:
        response = supabase.table("orders").select("*").eq("id", order_id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Order not found")
        order = response.data[0]
        items_resp = supabase.table("order_items").select("*").eq("order_id", order_id).execute()
        order["items"] = items_resp.data
        return order
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/orders", response_model=OrderResponse, status_code=201, tags=["Orders"])
def create_order(order: OrderCreate):
    """
    Create a new order with line items.

    - Use **GET /menu/names** to look up valid `menu_item_id` values.
    - Unit prices are fetched automatically from the menu.
    - Order total is computed automatically.
    """
    try:
        if not order.items:
            raise HTTPException(status_code=400, detail="Order must contain at least one item")

        # Resolve prices and compute total
        total = 0.0
        resolved_items = []
        for line in order.items:
            menu_resp = supabase.table("menu_items").select("price, available").eq("id", line.menu_item_id).execute()
            if not menu_resp.data:
                raise HTTPException(status_code=404, detail=f"Menu item {line.menu_item_id} not found")
            menu_item = menu_resp.data[0]
            if not menu_item["available"]:
                raise HTTPException(status_code=400, detail=f"Menu item {line.menu_item_id} is not available")
            unit_price = float(menu_item["price"])
            total += unit_price * line.quantity
            resolved_items.append({
                "menu_item_id": line.menu_item_id,
                "quantity": line.quantity,
                "unit_price": unit_price,
            })

        # Insert order
        order_resp = supabase.table("orders").insert({
            "customer_name": order.customer_name,
            "status": "pending",
            "total": round(total, 2),
        }).execute()
        new_order = order_resp.data[0]

        # Insert line items
        for li in resolved_items:
            li["order_id"] = new_order["id"]
        supabase.table("order_items").insert(resolved_items).execute()

        # Return full order with items
        items_resp = supabase.table("order_items").select("*").eq("order_id", new_order["id"]).execute()
        new_order["items"] = items_resp.data
        return new_order
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/orders/{order_id}", response_model=OrderResponse, tags=["Orders"])
def update_order(order_id: int, order: OrderUpdate):
    """
    Edit an existing order's customer name or status.

    Status options: `pending` → `confirmed` → `preparing` → `ready` → `delivered` / `cancelled`
    """
    try:
        check = supabase.table("orders").select("*").eq("id", order_id).execute()
        if not check.data:
            raise HTTPException(status_code=404, detail="Order not found")

        update_data = {k: v for k, v in order.model_dump().items() if v is not None}
        if not update_data:
            raise HTTPException(status_code=400, detail="No valid fields to update")

        response = supabase.table("orders").update(update_data).eq("id", order_id).execute()
        updated_order = response.data[0]

        items_resp = supabase.table("order_items").select("*").eq("order_id", order_id).execute()
        updated_order["items"] = items_resp.data
        return updated_order
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/orders/{order_id}", tags=["Orders"])
def delete_order(order_id: int):
    """Delete an order and all its line items (cascade)."""
    try:
        check = supabase.table("orders").select("id").eq("id", order_id).execute()
        if not check.data:
            raise HTTPException(status_code=404, detail="Order not found")
        supabase.table("orders").delete().eq("id", order_id).execute()
        return {"message": f"Order {order_id} and its items successfully deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
