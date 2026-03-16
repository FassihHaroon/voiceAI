import os
import streamlit as st
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

@st.cache_resource
def init_connection() -> Client:
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if not url or not key:
        st.error("Supabase URL or Key not found. Please set SUPABASE_URL and SUPABASE_KEY.")
        st.stop()
    return create_client(url, key)

supabase = init_connection()

st.set_page_config(page_title="KFC Menu Manager", page_icon="🍗")
st.title("🍗 KFC Menu Manager")
st.markdown("Manage your KFC menu items directly from this dashboard.")

CATEGORIES = ["Burgers", "Chicken", "Sides", "Drinks", "Desserts"]

# ----- Fetch & Display Menu -----
st.header("📋 Full Menu")

try:
    response = supabase.table("menu_items").select("*").order("category").execute()
    items = response.data

    if items:
        # Group by category
        from collections import defaultdict
        grouped = defaultdict(list)
        for item in items:
            grouped[item["category"]].append(item)

        for category, cat_items in grouped.items():
            st.subheader(f"🍴 {category}")
            for item in cat_items:
                col1, col2, col3 = st.columns([4, 1, 1])
                status = "✅" if item["available"] else "❌"
                col1.write(f"**{item['name']}** — {item.get('description', '')}")
                col2.write(f"**${item['price']:.2f}**")
                col3.write(f"{status}")
    else:
        st.info("No menu items found. Add some below!")

except Exception as e:
    st.error(f"Error fetching menu: {e}")

st.divider()

# ----- Add New Item -----
st.header("➕ Add New Menu Item")

with st.form("add_item_form"):
    col1, col2 = st.columns(2)
    new_name = col1.text_input("Item Name")
    new_category = col2.selectbox("Category", CATEGORIES)
    new_desc = st.text_area("Description", height=80)
    new_price = st.number_input("Price ($)", min_value=0.01, step=0.50, format="%.2f")
    new_available = st.checkbox("Available", value=True)
    submitted = st.form_submit_button("Add Item")

    if submitted:
        if new_name:
            try:
                supabase.table("menu_items").insert({
                    "name": new_name,
                    "category": new_category,
                    "description": new_desc,
                    "price": new_price,
                    "available": new_available
                }).execute()
                st.success(f"✅ Added '{new_name}' to {new_category}!")
                st.rerun()
            except Exception as e:
                st.error(f"Error adding item: {e}")
        else:
            st.warning("Please enter an item name.")

st.divider()

# ----- Update Item Availability -----
st.header("🔄 Toggle Availability")

if 'items' in locals() and items:
    item_options = {f"[{item['id']}] {item['name']} ({item['category']})": item for item in items}

    with st.form("toggle_form"):
        selected_label = st.selectbox("Select Item", list(item_options.keys()))
        selected_item = item_options[selected_label]
        new_status = st.checkbox("Mark as Available", value=selected_item["available"])
        toggle_submitted = st.form_submit_button("Update Availability")

        if toggle_submitted:
            try:
                supabase.table("menu_items").update({"available": new_status}).eq("id", selected_item["id"]).execute()
                st.success(f"Updated availability for '{selected_item['name']}'!")
                st.rerun()
            except Exception as e:
                st.error(f"Error updating: {e}")

st.divider()

# ----- Delete Item -----
st.header("🗑️ Delete Menu Item")

if 'items' in locals() and items:
    with st.form("delete_form"):
        del_options = {f"[{item['id']}] {item['name']} ({item['category']})": item['id'] for item in items}
        del_selected = st.selectbox("Select item to delete", list(del_options.keys()))
        del_submitted = st.form_submit_button("Delete Item", type="primary")

        if del_submitted:
            try:
                supabase.table("menu_items").delete().eq("id", del_options[del_selected]).execute()
                st.success("Item deleted!")
                st.rerun()
            except Exception as e:
                st.error(f"Error deleting: {e}")
