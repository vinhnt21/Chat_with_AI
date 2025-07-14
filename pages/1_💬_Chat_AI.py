import streamlit as st
import datetime
from utils.config import initialize_session_state, setup_sidebar, check_configuration
from utils.llm import get_llm_provider
from utils.db import get_all_prompts, save_chat_session

# --- Cấu hình trang ---
st.set_page_config(page_title="Chat AI", layout="wide")
initialize_session_state()
setup_sidebar()
check_configuration()

st.title("💬 Chat AI")

# --- Lấy provider và models ---
try:
    llm_provider = get_llm_provider(st.session_state.api_provider, st.session_state.api_key)
    available_models = llm_provider.get_models() if llm_provider else []
except (ValueError, Exception) as e:
    st.error(e)
    st.stop()

# --- Cài đặt cho phiên chat ---
col1, col2 = st.columns(2)
with col1:
    selected_model = st.selectbox("Chọn Model:", available_models)
with col2:
    prompts_data = get_all_prompts()
    prompt_options = {p['name']: p['content'] for p in prompts_data}
    prompt_names = ["-- Nhập thủ công --"] + list(prompt_options.keys())
    selected_prompt_name = st.selectbox("Chọn System Prompt có sẵn:", prompt_names)

if selected_prompt_name == "-- Nhập thủ công --":
    system_prompt = st.text_area("System Prompt:", "Bạn là một trợ lý AI hữu ích.", height=100)
else:
    system_prompt = st.text_area("System Prompt:", prompt_options[selected_prompt_name], height=100)

with st.expander("Cài đặt nâng cao"):
    temperature = st.slider("Temperature:", 0.0, 1.0, 0.7, 0.05)
    max_tokens = st.number_input("Max Tokens:", min_value=50, max_value=8192, value=2048)

# --- Hiển thị lịch sử chat ---
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- Xử lý input của người dùng ---
if user_prompt := st.chat_input("Nhập câu hỏi của bạn..."):
    st.session_state.chat_history.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.markdown(user_prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        try:
            response_stream = llm_provider.chat_stream(
                messages=st.session_state.chat_history,
                model=selected_model,
                temperature=temperature,
                max_tokens=max_tokens,
                system_prompt=system_prompt
            )
            for chunk in response_stream:
                full_response += chunk
                message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)
        except Exception as e:
            full_response = f"Lỗi: {e}"
            message_placeholder.error(full_response)

    st.session_state.chat_history.append({"role": "assistant", "content": full_response})

    session_to_save = {
        "_id": st.session_state.get("current_chat_session_id"),
        "session_name": f"Phiên chat lúc {datetime.datetime.now().strftime('%H:%M %d-%m-%Y')}",
        "api_provider": st.session_state.api_provider,
        "model": selected_model,
        "system_prompt": system_prompt,
        "history": st.session_state.chat_history
    }
    new_id = save_chat_session(session_to_save)
    if new_id:
        st.session_state.current_chat_session_id = new_id

# --- Nút chức năng ---
if st.button("Bắt đầu phiên chat mới"):
    st.session_state.chat_history = []
    st.session_state.current_chat_session_id = None
    st.rerun() 