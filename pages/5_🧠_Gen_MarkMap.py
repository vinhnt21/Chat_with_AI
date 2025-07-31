import streamlit as st
import io
import PyPDF2
from utils.config import initialize_session_state, setup_sidebar, check_configuration
from utils.llm import get_llm_provider
from utils.db import get_all_prompts

# --- Cấu hình trang ---
st.set_page_config(page_title="Markmap Generator", layout="wide")
initialize_session_state()
setup_sidebar()
check_configuration()

st.title("🧠 Markmap Generator")
st.write("Tạo mindmap (markmap) từ nội dung văn bản và files. Markmap là cú pháp tạo mindmap dựa trên Markdown.")

# Thông tin về Markmap
with st.expander("ℹ️ Thông tin về Markmap"):
    st.write("""
    **Markmap** là công cụ tạo mindmap tương tác từ Markdown. Cú pháp:
    
    ```markdown
    # Chủ đề chính
    ## Chủ đề con 1
    ### Chi tiết 1.1
    ### Chi tiết 1.2
    ## Chủ đề con 2
    ### Chi tiết 2.1
    ```
    
    Xem thêm tại: [markmap.js.org](https://markmap.js.org/)
    """)

# --- Lấy provider và models ---
try:
    llm_provider = get_llm_provider(st.session_state.api_provider, st.session_state.api_key)
    available_models = llm_provider.get_models() if llm_provider else []
except (ValueError, Exception) as e:
    st.error(f"Lỗi khởi tạo LLM provider: {e}")
    st.stop()

# --- Cấu hình Model và Prompts ---
with st.expander("⚙️ Cấu hình Model và Prompts", expanded=False):
    col1, col2 = st.columns(2)
    
    with col1:
        selected_model = st.selectbox("Chọn Model:", available_models, key="markmap_model")
        language = st.selectbox("Ngôn ngữ:", ["Tiếng Việt", "English"], key="markmap_language")
        
    with col2:
        temperature = st.slider("Temperature:", 0.0, 1.0, 0.3, 0.05, key="markmap_temp")
    
    # Custom Base Prompt
    st.write("**📝 Custom Base Prompt:**")
    use_custom_prompt = st.checkbox("Sử dụng custom prompt", key="use_custom_prompt")
    
    if use_custom_prompt:
        custom_base_prompt = st.text_area(
            "Base Prompt:",
            value="",
            height=150,
            key="custom_base_prompt",
            placeholder="Nhập custom prompt tại đây..."
        )
    else:
        # Default prompts based on language
        if language == "Tiếng Việt":
            default_prompt = """Bạn là một chuyên gia tạo mindmap. Hãy chuyển đổi CHÍNH XÁC nội dung người dùng nhập vào thành format Markmap (Markdown mindmap).

QUAN TRỌNG: 
- Sử dụng nội dung từ files đã upload CHỈ ĐỂ THAM KHẢO và hiểu ngữ cảnh
- CHỈ chuyển đổi nội dung trong phần "Nội dung nhập thủ công" thành markmap
- KHÔNG bao gồm nội dung từ files vào markmap cuối cùng

Yêu cầu:
1. Sử dụng cú pháp Markdown với headers (#, ##, ###, ...)
2. Tạo cấu trúc phân cấp logic và dễ hiểu
3. Tóm tắt thông tin quan trọng thành các nhánh chính
4. Sử dụng bullet points hoặc sub-headers cho chi tiết
5. Đảm bảo cấu trúc cân bằng và không quá sâu (tối đa 4-5 cấp)
6. Không cần bọc nội dung trong ```markdown ```, nội dung sẽ được dùng trực tiếp luôn

Format đầu ra phải là Markdown thuần túy có thể render thành mindmap."""
        else:
            default_prompt = """You are a mindmap expert. Convert EXACTLY the user's input content into Markmap (Markdown mindmap) format.

IMPORTANT: 
- Use uploaded files content ONLY FOR REFERENCE and context understanding
- ONLY convert content from "Manual input content" section into markmap
- DO NOT include file content in the final markmap

Requirements:
1. Use Markdown syntax with headers (#, ##, ###, ...)
2. Create logical and understandable hierarchical structure
3. Summarize important information into main branches
4. Use bullet points or sub-headers for details
5. Ensure balanced structure, not too deep (max 4-5 levels)
6. Do not wrap content in ```markdown ```, the content will be used directly

Output format must be pure Markdown that can be rendered as mindmap."""
        
        custom_base_prompt = st.text_area(
            "Base Prompt (Default):",
            value=default_prompt,
            height=150,
            key="default_base_prompt",
            disabled=True
        )

# --- Main Content ---
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📁 Upload Files & Nhập nội dung")
    
    # File upload section
    st.write("**Upload files liên quan:**")
    uploaded_files = st.file_uploader(
        "Chọn files (PDF, TXT, MD):",
        type=['pdf', 'txt', 'md'],
        accept_multiple_files=True,
        key="markmap_files"
    )
    
    # Hiển thị nội dung files đã upload
    uploaded_content = ""
    if uploaded_files:
        st.write("**Nội dung từ files:**")
        for uploaded_file in uploaded_files:
            file_content = ""
            try:
                if uploaded_file.type == "application/pdf":
                    # Đọc PDF
                    pdf_reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.read()))
                    for page in pdf_reader.pages:
                        file_content += page.extract_text() + "\n"
                else:
                    # Đọc TXT/MD
                    file_content = str(uploaded_file.read(), "utf-8")
                
                uploaded_content += f"\n=== Nội dung từ {uploaded_file.name} ===\n"
                uploaded_content += file_content + "\n"
                
                # Hiển thị preview
                with st.expander(f"📄 {uploaded_file.name} (Preview)"):
                    st.text_area("", file_content[:1000] + "..." if len(file_content) > 1000 else file_content, height=100, disabled=True)
                    
            except Exception as e:
                st.error(f"Lỗi đọc file {uploaded_file.name}: {e}")
    
    # Text input section
    st.write("**Nhập nội dung trực tiếp:**")
    manual_content = st.text_area(
        "Nội dung cần chuyển thành markmap:",
        height=200,
        placeholder="Nhập nội dung văn bản cần tạo mindmap...",
        key="markmap_content"
    )
    
    # Custom requirements
    st.write("**Yêu cầu tùy chỉnh:**")
    custom_requirements = st.text_area(
        "Yêu cầu cụ thể cho markmap:",
        height=100,
        placeholder="VD: Tập trung vào các khái niệm chính, tạo tối đa 5 nhánh chính, bao gồm ví dụ cụ thể...",
        key="markmap_requirements"
    )

with col2:
    st.subheader("🎯 Generate Markmap")
    
    # Markmap Configuration
    st.write("**⚙️ Cấu hình Markmap:**")
    default_config = """---
markmap:
  colorFreezeLevel: 2
  maxWidth: 300
  activeNode:
    placement: center
  initialExpandLevel: -1
---"""
    
    markmap_config = st.text_area(
        "Cấu hình YAML cho markmap:",
        value=default_config,
        height=150,
        key="markmap_config",
        help="Cấu hình này sẽ được thêm vào đầu markmap để tùy chỉnh hiển thị"
    )
    
    # Combine all content (chỉ để hiển thị context, không dùng để generate markmap)
    all_content = ""
    context_content = ""
    
    if uploaded_content.strip():
        context_content += uploaded_content
    
    if manual_content.strip():
        all_content = manual_content  # Chỉ nội dung manual được dùng để generate
        
    # Display context từ files nếu có
    if uploaded_content.strip() and manual_content.strip():
        st.info("📂 Files được upload sẽ dùng làm ngữ cảnh tham khảo. Chỉ nội dung nhập thủ công sẽ được chuyển thành markmap.")
    
    if st.button("🚀 Generate Markmap", type="primary", disabled=not all_content.strip()):
        if all_content.strip():
            with st.spinner("Đang tạo markmap..."):
                try:
                    # Sử dụng custom base prompt hoặc default
                    if use_custom_prompt and custom_base_prompt.strip():
                        base_prompt = custom_base_prompt
                    else:
                        base_prompt = default_prompt

                    # Thêm context từ files nếu có
                    if context_content.strip():
                        base_prompt += f"\n\n=== NGỮ CẢNH THAM KHẢO (từ files đã upload) ===\n{context_content}\n=== HẾT NGỮ CẢNH THAM KHẢO ===\n"
                    
                    if custom_requirements.strip():
                        base_prompt += f"\n\nYêu cầu bổ sung: {custom_requirements}"
                    
                    base_prompt += f"\n\nNội dung cần chuyển đổi thành markmap:\n{all_content}"
                    
                    # Generate với LLM
                    messages = [{"role": "user", "content": base_prompt}]
                    
                    # Stream response
                    response_text = ""
                    response_container = st.empty()
                    
                    system_prompt_text = "Bạn là chuyên gia tạo mindmap chuyên nghiệp. Luôn trả về format Markdown hoàn hảo cho markmap." if language == "Tiếng Việt" else "You are a professional mindmap expert. Always return perfect Markdown format for markmap."
                    
                    for chunk in llm_provider.chat_stream(
                        messages=messages,
                        model=selected_model,
                        temperature=temperature,
                        max_tokens=None,
                        system_prompt=system_prompt_text
                    ):
                        response_text += chunk
                        # Combine config with response for preview
                        full_markmap = f"{markmap_config.strip()}\n\n{response_text}"
                        response_container.markdown(f"**Markmap Result:**\n```markdown\n{full_markmap}\n```")
                    
                    # Final result with config
                    final_markmap = f"{markmap_config.strip()}\n\n{response_text}"
                    
                    # Hiển thị kết quả cuối cùng
                    st.success("✅ Đã tạo markmap thành công!")
                    
                  
                    
                    # Thông tin hướng dẫn sử dụng
                    with st.expander("💡 Cách sử dụng Markmap"):
                        st.write("""
                        **Cách sử dụng kết quả:**
                        1. Copy nội dung markmap ở trên
                        2. Vào [markmap.js.org/try](https://markmap.js.org/try)
                        3. Paste nội dung vào editor
                        4. Xem mindmap tương tác được tạo
                        
                        **Hoặc sử dụng trong VSCode:**
                        - Cài extension "Markmap for VSCode"
                        - Tạo file .md với nội dung trên
                        - Sử dụng command "Markmap: Open"
                        """)
                        
                except Exception as e:
                    st.error(f"Lỗi khi tạo markmap: {e}")
        else:
            st.warning("Vui lòng nhập nội dung hoặc upload file trước khi tạo markmap.")
    
    # Preview section nếu có nội dung
    if all_content.strip():
        with st.expander("👁️ Preview nội dung sẽ chuyển thành markmap"):
            st.text_area("", all_content[:2000] + "..." if len(all_content) > 2000 else all_content, height=200, disabled=True)
    
    # Preview context files nếu có
    if context_content.strip():
        with st.expander("📂 Preview ngữ cảnh từ files (chỉ tham khảo)"):
            st.text_area("", context_content[:1500] + "..." if len(context_content) > 1500 else context_content, height=150, disabled=True)
