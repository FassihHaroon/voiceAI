import os
import streamlit as st
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables from a .env file if it exists
load_dotenv()

# Initialize connection
@st.cache_resource
def init_connection() -> Client:
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    
    if not url or not key:
        st.error("Supabase URL or Key not found. Please set SUPABASE_URL and SUPABASE_KEY in your environment variables or a .env file.")
        st.stop()
        
    return create_client(url, key)

supabase = init_connection()

st.title("Supabase Dummy Database Frontend")

st.markdown("This app interacts with a dummy database table on Supabase.")
st.markdown("Expected table name: `items` with columns `id` (int8/uuid, primary key), `name` (text), and `description` (text).")

# Fetch data
st.header("Existing Items")

try:
    response = supabase.table("items").select("*").execute()
    items = response.data
    
    if items:
        st.dataframe(items)
    else:
        st.info("No items found. Add some below!")
        
except Exception as e:
    st.error(f"Error fetching data: {e}")

# Add new data
st.header("Add New Item")

with st.form("add_item_form"):
    new_name = st.text_input("Name")
    new_description = st.text_area("Description")
    submitted = st.form_submit_button("Add Item")
    
    if submitted:
        if new_name:
            try:
                # API call to insert data
                response = supabase.table("items").insert({"name": new_name, "description": new_description}).execute()
                st.success(f"Added item: {new_name}!")
                st.rerun()
            except Exception as e:
                st.error(f"Error adding data: {e}")
        else:
            st.warning("Please enter a name.")

# Delete data
st.header("Delete Item")

if 'items' in locals() and items:
    # Create a list of item IDs and Names to choose from
    item_options = {f"{item['id']} - {item['name']}": item['id'] for item in items}
    
    with st.form("delete_item_form"):
        selected_item = st.selectbox("Select item to delete", options=list(item_options.keys()))
        delete_submitted = st.form_submit_button("Delete Item")
        
        if delete_submitted and selected_item:
            try:
                # API call to delete data
                item_id = item_options[selected_item]
                response = supabase.table("items").delete().eq("id", item_id).execute()
                st.success(f"Deleted item!")
                st.rerun()
            except Exception as e:
                st.error(f"Error deleting data: {e}")
