import streamlit as st

def get_mongo_uri_for_key(user_key):
    """Lấy MongoDB URI tương ứng với user key từ secrets."""
    try:
        # Validate user key
        if user_key == st.secrets["USER_KEYS"]["ADMIN"]:
            return st.secrets["MONGODB"]["ADMIN_URI"], "ADMIN"
        elif user_key == st.secrets["USER_KEYS"]["GUEST"]:
            return st.secrets["MONGODB"]["GUEST_URI"], "GUEST"
        else:
            return None, None
    except KeyError:
        st.error("❌ Lỗi cấu hình secrets. Vui lòng liên hệ admin.")
        return None, None

def initialize_session_state():
    """Khởi tạo các giá trị cần thiết trong session_state nếu chúng chưa tồn tại."""
    defaults = {
        "user_key": None,
        "user_group": None,
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

        # Nhập user key thay vì MongoDB URI
        user_key_input = st.text_input(
            "🔐 User Key",
            type="password",
            value=st.session_state.get("user_key", ""),
            help="Nhập ADMIN hoặc GUEST key để truy cập"
        )
        
        # Validate user key và lấy MongoDB URI tương ứng
        if user_key_input:
            mongo_uri, user_group = get_mongo_uri_for_key(user_key_input)
            if mongo_uri:
                st.session_state.user_key = user_key_input
                st.session_state.user_group = user_group
                st.session_state.mongo_uri = mongo_uri
                st.success(f"✅ Key hợp lệ - Đang sử dụng {user_group} database")
            else:
                st.session_state.user_key = None
                st.session_state.user_group = None
                st.session_state.mongo_uri = None
                st.error("❌ User key không hợp lệ")
        else:
            st.session_state.user_key = None
            st.session_state.user_group = None
            st.session_state.mongo_uri = None

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
        
        # Hiển thị thông tin user hiện tại
        if st.session_state.get("user_group"):
            st.info(f"👤 User: {st.session_state.user_group}")
        
        if st.session_state.mongo_uri and st.session_state.api_key:
            st.success("Đã sẵn sàng để sử dụng!")
        else:
            st.warning("Vui lòng nhập đầy đủ cấu hình.")

def check_configuration():
    """Kiểm tra xem cấu hình đã được nhập chưa và hiển thị cảnh báo nếu cần."""
    if not st.session_state.get("api_key") or not st.session_state.get("user_key"):
        st.warning("Vui lòng nhập đầy đủ API Key và User Key trên thanh sidebar để bắt đầu.")
        st.stop() 