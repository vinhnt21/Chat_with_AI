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
                else:
                    st.error("Lỗi khi lưu prompt.")

with tab1:
    st.subheader("Danh sách prompts đã lưu")

    prompts_data = get_all_prompts()

    if not prompts_data:
        st.info("Chưa có prompt nào được lưu. Hãy tạo một prompt mới ở tab bên cạnh!")
    else:
        df = pd.DataFrame(prompts_data)
        df_display = df.rename(columns={
            '_id': 'ID', 'name': 'Tên Prompt', 'content': 'Nội dung', 'tags': 'Tags'
        })[['Tên Prompt', 'Nội dung', 'Tags', 'ID']]

        st.write("Bạn có thể chỉnh sửa trực tiếp trong bảng dưới đây. Thay đổi sẽ được tự động lưu.")

        edited_df = st.data_editor(
            df_display, key="prompts_editor", num_rows="dynamic", use_container_width=True,
            disabled=["ID"],
            column_config={"Nội dung": st.column_config.TextColumn(width="large")}
        )
        st.info("💡 Tính năng chỉnh sửa trực tiếp và xóa đang được phát triển.") 