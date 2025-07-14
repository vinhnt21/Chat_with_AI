import streamlit as st
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor
from utils.config import initialize_session_state, setup_sidebar, check_configuration
from utils.llm import get_llm_provider
from utils.db import get_all_prompts

# --- Cấu hình trang ---
st.set_page_config(page_title="Translation Tool", layout="wide")
initialize_session_state()
setup_sidebar()
check_configuration()

st.title("🌐 Công cụ Dịch thuật & Phân tích")
st.write("Sử dụng AI để dịch, tóm tắt và rút ra những điểm chính từ văn bản.")

# --- Lấy provider và models ---
try:
    llm_provider = get_llm_provider(st.session_state.api_provider, st.session_state.api_key)
    available_models = llm_provider.get_models() if llm_provider else []
except (ValueError, Exception) as e:
    st.error(f"Lỗi khởi tạo LLM provider: {e}")
    st.stop()

# --- Cấu hình cho translation tool ---
with st.expander("⚙️ Cấu hình Model và Prompts", expanded=False):
    col1, col2 = st.columns(2)
    
    with col1:
        selected_model = st.selectbox("Chọn Model:", available_models, key="trans_model")
        target_language = st.selectbox(
            "Ngôn ngữ đích:", 
            ["Vietnamese", "English", "French", "German", "Spanish", "Chinese", "Japanese", "Korean", "Thai"],
            key="target_lang"
        )
        
    with col2:
        temperature = st.slider("Temperature:", 0.0, 1.0, 0.3, 0.05, key="trans_temp")

# --- Custom Prompts Section ---
with st.expander("📝Custom Prompts"):



    # Lấy prompts đã lưu
    prompts_data = get_all_prompts()
    prompt_options = {p['name']: p['content'] for p in prompts_data}
    prompt_names = ["-- Tùy chỉnh --"] + list(prompt_options.keys())

    col1, col2, col3 = st.columns(3)

    with col1:
        st.write("**Prompt Dịch thuật:**")
        selected_translate_prompt = st.selectbox("Chọn prompt có sẵn:", prompt_names, key="trans_prompt_select")
        
        if selected_translate_prompt == "-- Tùy chỉnh --":
            translate_prompt = st.text_area(
                "Prompt dịch thuật:",
                f"Hãy dịch văn bản sau sang {target_language}. Giữ nguyên ý nghĩa và phong cách của văn bản gốc. Chỉ trả về bản dịch, không thêm giải thích:\n\n{{text}}",
                height=150,
                key="custom_trans_prompt"
            )
        else:
            translate_prompt = st.text_area(
                "Prompt dịch thuật:",
                prompt_options[selected_translate_prompt] + f"\n\nDịch sang {target_language}:\n{{text}}",
                height=150,
                key="custom_trans_prompt"
            )

    with col2:
        st.write("**Prompt Tóm tắt:**")
        selected_summary_prompt = st.selectbox("Chọn prompt có sẵn:", prompt_names, key="summary_prompt_select")
        
        if selected_summary_prompt == "-- Tùy chỉnh --":
            summary_prompt = st.text_area(
                "Prompt tóm tắt:",
                f"Hãy tóm tắt văn bản sau thành 3-5 câu chính bằng {target_language}. Tập trung vào những điểm quan trọng nhất:\n\n{{text}}",
                height=150,
                key="custom_summary_prompt"
            )
        else:
            summary_prompt = st.text_area(
                "Prompt tóm tắt:",
                prompt_options[selected_summary_prompt] + f"\n\nTóm tắt bằng {target_language}:\n{{text}}",
                height=150,
                key="custom_summary_prompt"
            )

    with col3:
        st.write("**Prompt Từ vựng hay:**")
        selected_vocab_prompt = st.selectbox("Chọn prompt có sẵn:", prompt_names, key="vocab_prompt_select")
        
        if selected_vocab_prompt == "-- Tùy chỉnh --":
            vocab_prompt = st.text_area(
                "Prompt từ vựng:",
                f"Từ văn bản sau, hãy trích xuất 5-10 từ/cụm từ hay và hữu ích nhất. Với mỗi từ, hãy cung cấp:\n- Từ gốc\n- Phiên âm (nếu cần)\n- Nghĩa bằng {target_language}\n- Ví dụ sử dụng\n\nVăn bản:\n{{text}}",
                height=150,
                key="custom_vocab_prompt"
            )
        else:
            vocab_prompt = st.text_area(
                "Prompt từ vựng:",
                prompt_options[selected_vocab_prompt] + f"\n\nTrích xuất từ vựng từ:\n{{text}}",
                height=150,
                key="custom_vocab_prompt"
            )

# --- Input Text ---
st.subheader("📄 Văn bản cần xử lý")
input_text = st.text_area("Dán văn bản gốc vào đây:", height=200, key="input_text")

# --- Processing Functions ---
def process_task(prompt_template, input_text, task_name):
    """Xử lý một task riêng lẻ với LLM provider"""
    try:
        # Format prompt với input text
        formatted_prompt = prompt_template.replace("{text}", input_text)
        messages = [{"role": "user", "content": formatted_prompt}]
        
        # Tạo response từ LLM
        response_stream = llm_provider.chat_stream(
            messages=messages,
            model=selected_model,
            temperature=temperature,
            system_prompt=f"Bạn là một chuyên gia {task_name}. Hãy thực hiện nhiệm vụ một cách chính xác và chi tiết."
        )
        
        # Collect full response
        full_response = ""
        for chunk in response_stream:
            if chunk:  # Check if chunk is not empty
                full_response += chunk
        
        # Check if response is empty or contains error messages
        if not full_response.strip():
            return f"⚠️ Không nhận được phản hồi cho {task_name}. Thử chuyển sang model khác."
        
        if full_response.strip().startswith("⚠️") or full_response.strip().startswith("❌"):
            return full_response.strip()
            
        return full_response.strip()
    except Exception as e:
        error_message = str(e)
        if "safety" in error_message.lower() or "finish_reason" in error_message:
            return f"⚠️ {task_name} bị chặn bởi bộ lọc an toàn. Vui lòng thử văn bản khác hoặc model khác."
        return f"❌ Lỗi xử lý {task_name}: {error_message}"

# --- Main Processing ---
if st.button("🚀 Phân tích ngay", type="primary", use_container_width=True):
    if not input_text.strip():
        st.error("Vui lòng nhập văn bản để phân tích.")
    else:
        # Process all tasks in parallel using ThreadPoolExecutor
        with st.spinner("AI đang xử lý tất cả các tác vụ, vui lòng chờ..."):
            with ThreadPoolExecutor(max_workers=3) as executor:
                # Submit all tasks
                future_translate = executor.submit(process_task, translate_prompt, input_text, "dịch thuật")
                future_summary = executor.submit(process_task, summary_prompt, input_text, "tóm tắt")
                future_vocab = executor.submit(process_task, vocab_prompt, input_text, "trích xuất từ vựng")
                
                # Get results
                translate_result = future_translate.result()
                summary_result = future_summary.result()
                vocab_result = future_vocab.result()
        
        # Display results in 2 columns
        col_results, col_original = st.columns([0.6, 0.4])
        
        with col_results:
            st.subheader("📊 Kết quả phân tích")
            # Create tabs for results
            tab1, tab2, tab3 = st.tabs(["🌐 Bản dịch", "📋 Tóm tắt", "📚 Từ vựng hay"])
            
            with tab1:
                st.write(f"**Bản dịch sang {target_language}:**")
                if translate_result.startswith("Lỗi"):
                    st.error(translate_result)
                else:
                    st.success("✅ Dịch thuật hoàn tất!")
                    st.markdown(translate_result)
                    
                    # Copy button
                    if st.button("📋 Copy bản dịch", key="copy_translate"):
                        st.code(translate_result)
            
            with tab2:
                st.write("**Tóm tắt nội dung:**")
                if summary_result.startswith("Lỗi"):
                    st.error(summary_result)
                else:
                    st.success("✅ Tóm tắt hoàn tất!")
                    st.info(summary_result)
                    
                    # Copy button
                    if st.button("📋 Copy tóm tắt", key="copy_summary"):
                        st.code(summary_result)
            
            with tab3:
                st.write("**Từ/Cụm từ đáng chú ý:**")
                if vocab_result.startswith("Lỗi"):
                    st.error(vocab_result)
                else:
                    st.success("✅ Trích xuất từ vựng hoàn tất!")
                    st.markdown(vocab_result)
                    
                    # Copy button
                    if st.button("📋 Copy từ vựng", key="copy_vocab"):
                        st.code(vocab_result)
        
        with col_original:
            st.subheader("📄 Văn bản gốc")
            st.write("*Được format để tiện so sánh:*")
            
            # Try to render as markdown first, fallback to plain text
            try:
                # Display as markdown for better formatting
                st.markdown("---")
                st.markdown(input_text)
                st.markdown("---")
                
                # Show text stats
                word_count = len(input_text.split())
                char_count = len(input_text)
                st.caption(f"📈 Thống kê: {word_count} từ, {char_count} ký tự")
                
                # Option to view as code/plain text
                if st.button("👁️ Xem dạng văn bản thuần", key="view_plain"):
                    st.code(input_text)
                    
            except Exception as e:
                # If markdown rendering fails, show as plain text
                st.text_area("Văn bản gốc:", input_text, height=300, disabled=True, key="original_text_display")

# --- Additional Features ---
with st.expander("💡 Hướng dẫn sử dụng"):
    st.markdown("""
    **Cách sử dụng công cụ dịch thuật:**
    
    1. **Cấu hình Model:** Chọn model AI phù hợp với nhu cầu của bạn
    2. **Chọn ngôn ngữ đích:** Chọn ngôn ngữ bạn muốn dịch sang
    3. **Tùy chỉnh Prompts:** 
       - Sử dụng prompts có sẵn từ Prompt Manager
       - Hoặc tự viết prompts theo nhu cầu cụ thể
       - Sử dụng `{text}` trong prompt để đánh dấu vị trí văn bản đầu vào
    4. **Nhập văn bản:** Paste văn bản cần xử lý vào ô input
    5. **Chạy phân tích:** Nhấn nút "Phân tích ngay" để xử lý
    
    **Mẹo:**
    - Các tác vụ sẽ chạy song song để tối ưu thời gian
    - Bạn có thể copy kết quả từ từng tab
    - Điều chỉnh temperature để kiểm soát độ sáng tạo (thấp = chính xác hơn)
    - Model khác nhau có thể cho kết quả khác nhau
    - AI sẽ dịch toàn bộ nội dung không giới hạn độ dài
    
    **⚠️ Xử lý lỗi Safety Filter:**
    - **Google Gemini** có bộ lọc an toàn strict, có thể chặn một số nội dung
    - Nếu gặp lỗi "bị chặn bởi bộ lọc an toàn":
      - Thử chuyển sang **OpenAI**, **Anthropic** hoặc **DeepSeek**
      - Hoặc điều chỉnh văn bản đầu vào để tránh từ ngữ nhạy cảm
      - Sử dụng prompts ít "directive" hơn
    """)

st.markdown("---")
st.info("💡 Tool này sử dụng AI để phân tích văn bản với khả năng tùy chỉnh cao.") 