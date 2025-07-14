import streamlit as st
from utils.config import initialize_session_state, setup_sidebar

# Thiết lập cấu hình trang
st.set_page_config(
    page_title="AI Tools Platform",
    page_icon="🚀",
    layout="wide"
)

# Khởi tạo session state và sidebar
initialize_session_state()
setup_sidebar()

# Define home page function
def home_page():
    st.title("🚀 Chào mừng đến với AI Tools Platform")
    st.markdown("---")
    st.subheader("Một bộ công cụ AI cá nhân, mạnh mẽ và linh hoạt.")

    st.markdown("""
    Đây là không gian làm việc cá nhân của bạn, tích hợp các mô hình ngôn ngữ hàng đầu để hỗ trợ công việc hàng ngày.

    **Các công cụ có sẵn:**

    - **💬 Chat AI:** Trò chuyện trực tiếp với các mô hình AI như GPT, Gemini, Claude, DeepSeek.
    - **🎨 Prompt Template Manager:** Tạo và quản lý các template prompt với biến động, render prompt tự động.
    - **📝 System Prompt Manager:** Tạo, lưu trữ và quản lý các System Prompt yêu thích của bạn.
    - **🌐 Translation Tool:** Dịch thuật, tóm tắt và phân tích văn bản chuyên sâu.

    **Để bắt đầu:**

    1.  **Nhập cấu hình:** Mở thanh sidebar bên trái (nếu đang ẩn).
    2.  **Nhập `User Key`:** Sử dụng key ADMIN hoặc GUEST để truy cập vào database riêng biệt.
    3.  **Chọn `Nhà cung cấp API` và dán `API Key` tương ứng.**
    4.  **Khám phá các công cụ!**

    **Lưu ý:** Mỗi User Key có dữ liệu riêng biệt:
    - **ADMIN:** Có quyền truy cập đầy đủ với database riêng
    - **GUEST:** Có quyền truy cập cơ bản với database riêng
    
    Tất cả dữ liệu được phân tách hoàn toàn giữa các user group.
    """)

    st.info("💡 **Mẹo:** Bạn có thể chuyển đổi giữa các công cụ bằng cách sử dụng thanh điều hướng bên trái.")

# Define navigation pages
pages = [
    st.Page(home_page, title="Home", icon="🏠", default=True),
    st.Page("pages/3_🌐_Translation_Tool.py", title="Translation Tool", icon="🌐"),
    st.Page("pages/4_🎨_Prompt_Template_Manager.py", title="Prompt Template Manager", icon="🎨"),
    st.Page("pages/2_📝_System_Prompt_Manager.py", title="System Prompt Manager", icon="📝"),    
    st.Page("pages/1_💬_Chat_AI.py", title="Chat AI", icon="💬"),
]

# Create navigation
pg = st.navigation(pages, position="sidebar", expanded=True)

# Run the selected page
pg.run() 