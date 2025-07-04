import streamlit as st
import os
from google import genai
from google.genai import types
from datetime import datetime
import tempfile


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

# File upload section
with st.expander("📎 Gửi file (ảnh, âm thanh, video, PDF...)", expanded=False):
    uploaded_file = st.file_uploader(
        "Chọn file để gửi",
        type=['jpg', 'jpeg', 'png', 'gif', 'webp', 'mp3', 'wav', 'mp4', 'avi', 'mov', 'pdf', 'txt', 'doc', 'docx'],
        help="Hỗ trợ: ảnh (JPG, PNG, GIF, WebP), âm thanh (MP3, WAV), video (MP4, AVI, MOV), tài liệu (PDF, TXT, DOC, DOCX)"
    )
    
    # File description input
    if uploaded_file:
        file_description = st.text_input(
            "Mô tả hoặc câu hỏi về file (tùy chọn)",
            placeholder="Ví dụ: Hãy mô tả ảnh này, Phân tích nội dung audio...",
            key="file_description"
        )
        
        # Send file button
        send_file = st.button("📤 Gửi file", type="primary", use_container_width=True)
    else:
        send_file = False
        file_description = ""

# Display chat history
chat_container = st.container()
with chat_container:
    for message in st.session_state.chat_history:
        if message["role"] == "user":
            with st.chat_message("user"):
                # Display text content
                if message.get("content"):
                    st.write(message["content"])
                
                # Display file info if exists
                if message.get("file_info"):
                    file_info = message["file_info"]
                    st.info(f"📎 File: {file_info['name']} ({file_info['size']} bytes)")
                    
                    # Show image preview if it's an image
                    if file_info.get("type", "").startswith("image/"):
                        if file_info.get("local_path") and os.path.exists(file_info["local_path"]):
                            st.image(file_info["local_path"], width=300)
        else:
            with st.chat_message("assistant"):
                st.write(message["content"])

# Chat input
user_input = st.chat_input("Nhập tin nhắn của bạn...")

# Function to generate response
def generate_response(client, model, chat_history, temp, thinking_budget_val, uploaded_file_obj=None):
    # Convert chat history to Contents format for the API
    contents = []
    
    for message in chat_history:
        if message["role"] == "user":
            parts = [types.Part.from_text(text=message["content"])]
            
            # Add file if this message has one
            if message.get("gemini_file"):
                parts.append(message["gemini_file"])
            
            contents.append(
                types.Content(
                    role="user",
                    parts=parts,
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

def upload_file_to_gemini(client, file_path, file_name):
    """Upload file to Gemini and return file object"""
    try:
        uploaded_file = client.files.upload(file=file_path)
        return uploaded_file
    except Exception as e:
        st.error(f"❌ Lỗi khi upload file: {str(e)}")
        return None

# Process file upload
if send_file and uploaded_file and api_key:
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{uploaded_file.name}") as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_file_path = tmp_file.name
        
        # Initialize client
        client = genai.Client(api_key=api_key)
        
        # Upload file to Gemini
        with st.spinner("📤 Đang upload file..."):
            gemini_file = upload_file_to_gemini(client, tmp_file_path, uploaded_file.name)
        
        if gemini_file:
            # Prepare message content
            message_content = file_description if file_description else f"Đây là file {uploaded_file.name}"
            
            # Add user message with file to chat history
            file_info = {
                "name": uploaded_file.name,
                "size": uploaded_file.size,
                "type": uploaded_file.type,
                "local_path": tmp_file_path if uploaded_file.type.startswith("image/") else None
            }
            
            st.session_state.chat_history.append({
                "role": "user",
                "content": message_content,
                "file_info": file_info,
                "gemini_file": gemini_file
            })
            
            # Display user message with file
            with st.chat_message("user"):
                st.write(message_content)
                st.info(f"📎 File: {uploaded_file.name} ({uploaded_file.size} bytes)")
                
                # Show image preview if it's an image
                if uploaded_file.type.startswith("image/"):
                    st.image(uploaded_file, width=300)
            
            # Generate and display AI response
            with st.chat_message("assistant"):
                try:
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
                    st.error(f"❌ Lỗi khi xử lý file: {str(e)}")
        
        # Clean up temporary file after a delay (keep for image preview)
        if not uploaded_file.type.startswith("image/"):
            try:
                os.unlink(tmp_file_path)
            except:
                pass
                
    except Exception as e:
        st.error(f"❌ Lỗi khi xử lý file: {str(e)}")
    
    # Clear the file uploader by rerunning
    st.rerun()

elif send_file and not api_key:
    st.warning("⚠️ Vui lòng nhập API key trong sidebar để gửi file!")

elif send_file and not uploaded_file:
    st.warning("⚠️ Vui lòng chọn file để gửi!")

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
    4. **Chat văn bản**: Nhập tin nhắn và nhấn Enter để chat
    5. **Gửi file**: Sử dụng phần "📎 Gửi file" để upload và phân tích file
    
    **Lấy API Key:**
    - Truy cập [Google AI Studio](https://aistudio.google.com/apikey)
    - Tạo API key mới
    - Copy và paste vào ứng dụng
    
    **Models có sẵn:**
    - `gemini-2.5-pro`: Model mạnh nhất, phù hợp cho các tác vụ phức tạp
    - `gemini-2.5-flash`: Model nhanh, phù hợp cho chat thông thường
    
    **File được hỗ trợ:**
    - **Ảnh**: JPG, PNG, GIF, WebP
    - **Âm thanh**: MP3, WAV
    - **Video**: MP4, AVI, MOV
    - **Tài liệu**: PDF, TXT, DOC, DOCX
    
    **Mẹo sử dụng file:**
    - Thêm mô tả cụ thể cho file để được phản hồi chính xác hơn
    - Ví dụ: "Mô tả chi tiết nội dung ảnh này", "Tóm tắt nội dung audio"
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