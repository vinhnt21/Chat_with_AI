import streamlit as st
import os
from google import genai
from google.genai import types
from datetime import datetime


# Cấu hình trang
st.set_page_config(
    page_title="DeepSeek",
    page_icon="🤖",
    layout="wide"
)

# Khởi tạo session state variables
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "conversation_start_time" not in st.session_state:
    st.session_state.conversation_start_time = datetime.now().strftime("%Y%m%d_%H%M%S")

# Title
st.title("🤖 DeepSeek Chat")
st.markdown("---")

# Sidebar cho cấu hình
with st.sidebar:
    st.header("⚙️ Cấu hình")
    
    # API Key input
    api_key = st.text_input(
        "🔑 Gemini API Key",
        type="password",
        help="Nhập API key của bạn để sử dụng Gemini API"
    )
    
    # Model selection
    model_options = [
        "gemini-2.5-pro",
        "gemini-2.5-flash"
    ]
    selected_model = st.selectbox(
        "🤖 Chọn Model",
        model_options,
        index=0
    )
    
    # Temperature slider
    temperature = st.slider(
        "🌡️ Temperature",
        min_value=0.0,
        max_value=2.0,
        value=1.0,
        step=0.1,
        help="Độ sáng tạo của AI (0.0 = conservative, 2.0 = creative)"
    )
    
    # Thinking budget
    thinking_budget = st.slider(
        "🧠 Thinking Budget",
        min_value=-1,
        max_value=100,
        value=-1,
        help="Thời gian suy nghĩ của AI (-1 = không giới hạn)"
    )
    
    # Clear chat button
    if st.button("🗑️ Xóa lịch sử chat", use_container_width=True):
        st.session_state.chat_history = []
        st.session_state.conversation_start_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        st.rerun()
    
    # Chat history info
    st.markdown("---")
    st.subheader("📊 Thông tin Chat")
    
    if st.session_state.chat_history:
        total_messages = len(st.session_state.chat_history)
        user_messages = len([msg for msg in st.session_state.chat_history if msg["role"] == "user"])
        ai_messages = len([msg for msg in st.session_state.chat_history if msg["role"] == "assistant"])
        
        st.metric("Tổng tin nhắn", total_messages)
        st.metric("Tin nhắn của bạn", user_messages)
        st.metric("Phản hồi AI", ai_messages)
        
        # Export chat history
        if st.button("📥 Xuất lịch sử chat", use_container_width=True):
            chat_export = "\n".join([
                f"{'🧑‍💻 User' if msg['role'] == 'user' else '🤖 AI'}: {msg['content']}\n"
                for msg in st.session_state.chat_history
            ])
            st.download_button(
                label="💾 Tải về file text",
                data=chat_export,
                file_name=f"chat_history_{st.session_state.conversation_start_time}.txt",
                mime="text/plain",
                use_container_width=True
            )
    else:
        st.info("Chưa có tin nhắn nào")
    
    st.markdown("---")

# Main chat interface
st.header("💬 Chat")

# Display chat history
chat_container = st.container()
with chat_container:
    for message in st.session_state.chat_history:
        if message["role"] == "user":
            with st.chat_message("user"):
                st.write(message["content"])
        else:
            with st.chat_message("assistant"):
                st.write(message["content"])

# Chat input
user_input = st.chat_input("Nhập tin nhắn của bạn...")

# Function to generate response
def generate_response(client, model, chat_history, temp, thinking_budget_val):
    # Convert chat history to Contents format for the API
    contents = []
    
    for message in chat_history:
        if message["role"] == "user":
            contents.append(
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=message["content"])],
                )
            )
        elif message["role"] == "assistant":
            contents.append(
                types.Content(
                    role="model",  # Gemini uses "model" instead of "assistant"
                    parts=[types.Part.from_text(text=message["content"])],
                )
            )
    
    generate_content_config = types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(
            thinking_budget=thinking_budget_val,
        ),
        response_mime_type="text/plain",
        temperature=temp,
    )
    
    return client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    )

# Process user input
if user_input and api_key:
    # Add user message to chat history
    st.session_state.chat_history.append({
        "role": "user",
        "content": user_input
    })
    
    # Display user message
    with st.chat_message("user"):
        st.write(user_input)
    
    # Generate and display AI response
    with st.chat_message("assistant"):
        try:
            # Initialize client
            client = genai.Client(api_key=api_key)
            
            # Create placeholder for streaming response
            response_placeholder = st.empty()
            full_response = ""
            
            # Generate streaming response
            stream = generate_response(
                client, 
                selected_model, 
                st.session_state.chat_history, 
                temperature, 
                thinking_budget
            )
            
            # Stream the response
            for chunk in stream:
                if chunk.text:
                    full_response += chunk.text
                    response_placeholder.write(full_response)
            
            # Add AI response to chat history
            st.session_state.chat_history.append({
                "role": "assistant", 
                "content": full_response
            })
            
        except Exception as e:
            st.error(f"❌ Lỗi: {str(e)}")
            st.error("Vui lòng kiểm tra API key và thử lại.")

elif user_input and not api_key:
    st.warning("⚠️ Vui lòng nhập API key trong sidebar để sử dụng!")

# Information section
with st.expander("ℹ️ Hướng dẫn sử dụng"):
    st.markdown("""
    **Cách sử dụng ứng dụng:**
    
    1. **Nhập API Key**: Trong sidebar, nhập API key Gemini của bạn
    2. **Chọn Model**: Chọn model Gemini phù hợp
    3. **Điều chỉnh Temperature**: Thay đổi độ sáng tạo của AI
    4. **Chat**: Nhập tin nhắn và nhấn Enter để chat
    
    **Lấy API Key:**
    - Truy cập [Google AI Studio](https://aistudio.google.com/apikey)
    - Tạo API key mới
    - Copy và paste vào ứng dụng
    
    **Models có sẵn:**
    - `gemini-2.5-pro`: Model mạnh nhất, phù hợp cho các tác vụ phức tạp
    - `gemini-2.5-flash`: Model nhanh, phù hợp cho chat thông thường
    """)

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>"
    "Được xây dựng với ❤️ sử dụng Streamlit và Gemini API/"
    "AIzaSyDTxyIyE_j-6-K_FycZKcLJsAiZNy----/"
    "AIzaSyCaFFTGjFLPojwbglFRuwLS3-Q-aXk----/"
    "AIzaSyAaCUt4nMWM43fILvu3RS0ADQZufMN----/"

    "</div>", 
    unsafe_allow_html=True
) 