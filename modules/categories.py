import streamlit as st
import database as db
from modules import utils

def view():
    st.header("類別管理")

    # Add New Category
    with st.expander("新增類別", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            category_name = st.text_input("類別名稱")
        
        with col2:
            category_type_display = st.selectbox("類型", ["支出", "收入", "兩者皆可"])
            category_type_map = {"支出": "Expense", "收入": "Income", "兩者皆可": "Both"}
            category_type = category_type_map[category_type_display]
        
        if st.button("新增類別"):
            if category_name:
                success = db.add_category(category_name, category_type)
                if success:
                    st.success(f"類別 '{category_name}' 新增成功！")
                    st.rerun()
                else:
                    st.error(f"類別 '{category_name}' 已存在。")
            else:
                st.error("請輸入類別名稱。")

    # View Categories
    st.subheader("現有類別")
    df = db.get_categories()
    
    if not df.empty:
        # Display categories in a nice format
        display_df = df[['id', 'name', 'type']].copy()
        type_map = {"Expense": "支出", "Income": "收入", "Both": "兩者皆可"}
        display_df['type'] = display_df['type'].map(type_map)
        display_df.columns = ['ID', '類別名稱', '類型']
        st.dataframe(display_df, use_container_width=True)
        
        # Delete Category
        with st.expander("刪除類別"):
            category_id_to_delete = st.number_input(
                "輸入要刪除的類別 ID", 
                min_value=1, 
                step=1, 
                key="delete_category_id"
            )
            
            if st.button("刪除", key="delete_category_btn"):
                # Check if category is in use
                transactions_df = db.get_all_transactions()
                if not transactions_df.empty:
                    category_to_delete = df[df['id'] == category_id_to_delete]
                    if not category_to_delete.empty:
                        category_name = category_to_delete.iloc[0]['name']
                        if category_name in transactions_df['category'].values:
                            st.error(f"無法刪除類別 '{category_name}'，因為它正在交易中使用。")
                        else:
                            db.delete_category(category_id_to_delete)
                            st.success(f"類別 {category_id_to_delete} 已成功刪除！")
                            st.rerun()
                    else:
                        st.error("找不到該類別 ID。")
                else:
                    db.delete_category(category_id_to_delete)
                    st.success(f"類別 {category_id_to_delete} 已成功刪除！")
                    st.rerun()
    else:
        st.info("找不到類別。請在上方新增第一個類別！")
