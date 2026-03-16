import os
from fastapi.responses import RedirectResponse
from fastapi import FastAPI, HTTPException
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
    title="KFC Menu API",
    description="APIs to interact with the KFC menu database on Supabase",
    version="1.0.0"
)

# Pydantic models
class MenuItemCreate(BaseModel):
    name: str
    category: str
    description: Optional[str] = None
    price: float
    available: Optional[bool] = True

class MenuItemUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
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

@app.get("/", include_in_schema=False)
def root():
    """Redirect root URL to Swagger docs."""
    return RedirectResponse(url="/docs")

@app.get("/menu", response_model=list[MenuItemResponse], tags=["Menu"])
def get_menu():
    """Fetch all KFC menu items."""
    try:
        response = supabase.table("menu_items").select("*").order("category").execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/menu/category/{category}", response_model=list[MenuItemResponse], tags=["Menu"])
def get_by_category(category: str):
    """Fetch menu items by category (e.g. Burgers, Chicken, Sides, Drinks, Desserts)."""
    try:
        response = supabase.table("menu_items").select("*").eq("category", category).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail=f"No items found in category '{category}'")
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
