import streamlit as st

def initialize_session_state():
    """Khởi tạo các giá trị cần thiết trong session_state nếu chúng chưa tồn tại."""
    defaults = {
        "mongo_uri": None,
        "api_provider": "Google",
        "api_key": None,
        "db_client": None,
        "chat_history": [],
        "current_chat_session_id": None
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def setup_sidebar():
    """Hiển thị sidebar để nhập cấu hình và lưu vào session_state."""
    with st.sidebar:
        st.header("⚙️ Cấu hình")

        st.session_state.mongo_uri = st.text_input(
            "🔗 MongoDB URI",
            type="password",
            value=st.session_state.get("mongo_uri", "")
        )

        # Cập nhật danh sách nhà cung cấp
        providers = ["OpenAI", "Google", "Anthropic", "DeepSeek"]
        st.session_state.api_provider = st.selectbox(
            "🤖 Nhà cung cấp API",
            providers,
            index=providers.index(st.session_state.get("api_provider", "OpenAI"))
        )

        st.session_state.api_key = st.text_input(
            f"🔑 API Key cho {st.session_state.api_provider}",
            type="password",
            value=st.session_state.get("api_key", "")
        )

        st.markdown("---")
        if st.session_state.mongo_uri and st.session_state.api_key:
            st.success("Đã sẵn sàng để sử dụng!")
        else:
            st.warning("Vui lòng nhập đầy đủ cấu hình.")

def check_configuration():
    """Kiểm tra xem cấu hình đã được nhập chưa và hiển thị cảnh báo nếu cần."""
    if not st.session_state.get("api_key") or not st.session_state.get("mongo_uri"):
        st.warning("Vui lòng nhập đầy đủ API Key và MongoDB URI trên thanh sidebar để bắt đầu.")
        st.stop() 