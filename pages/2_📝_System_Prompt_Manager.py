import streamlit as st
import pandas as pd
from utils.config import initialize_session_state, setup_sidebar, check_configuration
from utils.db import get_all_prompts, save_prompt, update_prompt, delete_prompt

# --- Cấu hình trang ---
st.set_page_config(page_title="Prompt Manager", layout="wide")
initialize_session_state()
setup_sidebar()
check_configuration()

st.title("📝 Trình quản lý System Prompt")
st.write("Tạo, chỉnh sửa và quản lý các prompt mẫu của bạn.")

# --- Tab: Tạo prompt mới và Quản lý ---
tab1, tab2 = st.tabs(["Quản lý Prompts", "➕ Tạo Prompt Mới"])

with tab2:
    st.subheader("Tạo một prompt mới")
    with st.form("new_prompt_form", clear_on_submit=True):
        name = st.text_input("Tên gợi nhớ cho prompt:")
        content = st.text_area("Nội dung prompt:", height=200)
        tags_input = st.text_input("Tags (phân cách bởi dấu phẩy):")

        submitted = st.form_submit_button("Lưu Prompt")
        if submitted:
            if not name or not content:
                st.error("Tên và nội dung không được để trống!")
            else:
                tags = [tag.strip() for tag in tags_input.split(",")] if tags_input else []
                if save_prompt(name, content, tags):
                    st.success("Đã lưu prompt thành công!")
                    st.rerun()
                else:
                    st.error("Lỗi khi lưu prompt.")

with tab1:
    st.subheader("Danh sách prompts đã lưu")

    prompts_data = get_all_prompts()

    if not prompts_data:
        st.info("Chưa có prompt nào được lưu. Hãy tạo một prompt mới ở tab bên cạnh!")
    else:
        # Hiển thị từng prompt với các nút sửa/xóa
        for i, prompt in enumerate(prompts_data):
            with st.container():
                col1, col2, col3 = st.columns([6, 1, 1])
                
                with col1:
                    st.write(f"**{prompt['name']}**")
                    # Hiển thị một phần nội dung (100 ký tự đầu)
                    preview = prompt['content'][:100] + "..." if len(prompt['content']) > 100 else prompt['content']
                    st.write(f"📝 {preview}")
                    if prompt.get('tags'):
                        tags_str = ", ".join(prompt['tags'])
                        st.write(f"🏷️ Tags: {tags_str}")
                
                with col2:
                    if st.button("✏️ Sửa", key=f"edit_{i}"):
                        st.session_state[f"editing_{prompt['_id']}"] = True
                        st.rerun()
                
                with col3:
                    if st.button("🗑️ Xóa", key=f"delete_{i}"):
                        st.session_state[f"confirm_delete_{prompt['_id']}"] = True
                        st.rerun()
                
                # Form sửa prompt (hiển thị khi nhấn nút Sửa)
                if st.session_state.get(f"editing_{prompt['_id']}", False):
                    with st.expander("✏️ Chỉnh sửa prompt", expanded=True):
                        with st.form(f"edit_form_{prompt['_id']}"):
                            edit_name = st.text_input("Tên prompt:", value=prompt['name'], key=f"edit_name_{i}")
                            edit_content = st.text_area("Nội dung:", value=prompt['content'], height=200, key=f"edit_content_{i}")
                            current_tags = ", ".join(prompt.get('tags', []))
                            edit_tags = st.text_input("Tags (phân cách bởi dấu phẩy):", value=current_tags, key=f"edit_tags_{i}")
                            
                            col_save, col_cancel = st.columns(2)
                            with col_save:
                                if st.form_submit_button("💾 Lưu thay đổi"):
                                    if edit_name and edit_content:
                                        tags_list = [tag.strip() for tag in edit_tags.split(",")] if edit_tags else []
                                        update_data = {
                                            "name": edit_name,
                                            "content": edit_content,
                                            "tags": tags_list
                                        }
                                        if update_prompt(str(prompt['_id']), update_data):
                                            st.success("Đã cập nhật prompt thành công!")
                                            st.session_state[f"editing_{prompt['_id']}"] = False
                                            st.rerun()
                                        else:
                                            st.error("Lỗi khi cập nhật prompt.")
                                    else:
                                        st.error("Tên và nội dung không được để trống!")
                            
                            with col_cancel:
                                if st.form_submit_button("❌ Hủy"):
                                    st.session_state[f"editing_{prompt['_id']}"] = False
                                    st.rerun()
                
                # Xác nhận xóa
                if st.session_state.get(f"confirm_delete_{prompt['_id']}", False):
                    st.warning(f"⚠️ Bạn có chắc chắn muốn xóa prompt **{prompt['name']}**?")
                    col_confirm, col_cancel_del = st.columns(2)
                    
                    with col_confirm:
                        if st.button("✅ Xác nhận xóa", key=f"confirm_yes_{i}"):
                            if delete_prompt(str(prompt['_id'])):
                                st.success("Đã xóa prompt thành công!")
                                st.session_state[f"confirm_delete_{prompt['_id']}"] = False
                                st.rerun()
                            else:
                                st.error("Lỗi khi xóa prompt.")
                    
                    with col_cancel_del:
                        if st.button("❌ Hủy xóa", key=f"confirm_no_{i}"):
                            st.session_state[f"confirm_delete_{prompt['_id']}"] = False
                            st.rerun()
                
                st.divider() 