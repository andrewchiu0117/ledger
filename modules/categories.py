import streamlit as st
import database as db
from modules import utils

def view():
    st.header("Category Management")

    # Add New Category
    with st.expander("Add New Category", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            category_name = st.text_input("Category Name")
        
        with col2:
            category_type = st.selectbox("Type", ["Expense", "Income", "Both"])
        
        if st.button("Add Category"):
            if category_name:
                success = db.add_category(category_name, category_type)
                if success:
                    st.success(f"Category '{category_name}' added successfully!")
                    st.rerun()
                else:
                    st.error(f"Category '{category_name}' already exists.")
            else:
                st.error("Please enter a category name.")

    # View Categories
    st.subheader("Existing Categories")
    df = db.get_categories()
    
    if not df.empty:
        # Display categories in a nice format
        st.dataframe(df[['id', 'name', 'type']], use_container_width=True)
        
        # Delete Category
        with st.expander("Delete Category"):
            category_id_to_delete = st.number_input(
                "Enter Category ID to delete", 
                min_value=1, 
                step=1, 
                key="delete_category_id"
            )
            
            if st.button("Delete", key="delete_category_btn"):
                # Check if category is in use
                transactions_df = db.get_all_transactions()
                if not transactions_df.empty:
                    category_to_delete = df[df['id'] == category_id_to_delete]
                    if not category_to_delete.empty:
                        category_name = category_to_delete.iloc[0]['name']
                        if category_name in transactions_df['category'].values:
                            st.error(f"Cannot delete category '{category_name}' as it is being used in transactions.")
                        else:
                            db.delete_category(category_id_to_delete)
                            st.success(f"Category {category_id_to_delete} deleted successfully!")
                            st.rerun()
                    else:
                        st.error("Category ID not found.")
                else:
                    db.delete_category(category_id_to_delete)
                    st.success(f"Category {category_id_to_delete} deleted successfully!")
                    st.rerun()
    else:
        st.info("No categories found. Add your first category above!")
