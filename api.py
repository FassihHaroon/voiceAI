import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from supabase import create_client, Client
from dotenv import load_dotenv

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
    title="Supabase Dummy API",
    description="Local APIs to interact with Supabase items table",
    version="1.0.0"
)

# Pydantic models for data validation and Swagger UI schemas
class ItemCreate(BaseModel):
    name: str
    description: str | None = None

class ItemUpdate(BaseModel):
    name: str | None = None
    description: str | None = None

class ItemResponse(BaseModel):
    id: int
    name: str
    description: str | None = None

@app.get("/items", response_model=list[ItemResponse], tags=["Items"])
def get_items():
    """Fetch all items from the database."""
    try:
        response = supabase.table("items").select("*").execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/items/{item_id}", response_model=list[ItemResponse], tags=["Items"])
def get_item(item_id: int):
    """Fetch a single item by ID."""
    try:
        response = supabase.table("items").select("*").eq("id", item_id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Item not found")
        return response.data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/items", response_model=list[ItemResponse], status_code=201, tags=["Items"])
def create_item(item: ItemCreate):
    """Create a new item in the database."""
    try:
        response = supabase.table("items").insert(item.model_dump()).execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/items/{item_id}", response_model=list[ItemResponse], tags=["Items"])
def update_item(item_id: int, item: ItemUpdate):
    """Update an existing item by ID."""
    try:
        update_data = {k: v for k, v in item.model_dump().items() if v is not None}
        if not update_data:
             raise HTTPException(status_code=400, detail="No valid fields to update")

        response = supabase.table("items").update(update_data).eq("id", item_id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Item not found or no changes made")
        return response.data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/items/{item_id}", tags=["Items"])
def delete_item(item_id: int):
    """Delete an item by ID."""
    try:
         # Need to check if it exists first to return a proper 404
        check = supabase.table("items").select("*").eq("id", item_id).execute()
        if not check.data:
            raise HTTPException(status_code=404, detail="Item not found")

        response = supabase.table("items").delete().eq("id", item_id).execute()
        return {"message": f"Item {item_id} successfully deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Running instructions:
# uvicorn api:app --reload
