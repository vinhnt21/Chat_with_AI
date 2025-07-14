import streamlit as st
import datetime
import json
from utils.config import initialize_session_state, setup_sidebar, check_configuration
from utils.llm import get_llm_provider
from utils.db import get_all_prompts, save_chat_session, get_all_chat_sessions, get_chat_session, delete_chat_session

# --- Cấu hình trang ---
st.set_page_config(page_title="Chat AI", layout="wide")
initialize_session_state()
setup_sidebar()
check_configuration()

st.title("💬 Chat AI")

# --- Tạo tabs ---
tab1, tab2, tab3 = st.tabs(["💬 Chat", "📚 Lịch sử Chat", "📊 Xuất & Tóm tắt"])

with tab1:
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
        
        # Max tokens option
        use_max_tokens = st.checkbox("Giới hạn Max Tokens", value=False)
        max_tokens = None
        if use_max_tokens:
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
    if st.button("🆕 Bắt đầu phiên chat mới"):
        st.session_state.chat_history = []
        st.session_state.current_chat_session_id = None
        st.rerun()

with tab2:
    st.subheader("📚 Lịch sử các phiên chat")
    
    chat_sessions = get_all_chat_sessions()
    
    if not chat_sessions:
        st.info("Chưa có phiên chat nào được lưu. Hãy bắt đầu chat ở tab bên cạnh!")
    else:
        st.write(f"Tìm thấy {len(chat_sessions)} phiên chat đã lưu:")
        
        for i, session in enumerate(chat_sessions):
            with st.container():
                col1, col2, col3, col4 = st.columns([4, 1, 1, 1])
                
                with col1:
                    # Hiển thị thông tin session
                    st.write(f"**{session.get('session_name', 'Phiên chat')}**")
                    created_time = session.get('created_at', datetime.datetime.now())
                    if isinstance(created_time, datetime.datetime):
                        time_str = created_time.strftime('%d/%m/%Y %H:%M')
                    else:
                        time_str = str(created_time)
                    st.write(f"📅 {time_str}")
                    st.write(f"🤖 {session.get('api_provider', 'N/A')} - {session.get('model', 'N/A')}")
                    
                    # Hiển thị preview của tin nhắn cuối
                    history = session.get('history', [])
                    if history:
                        last_msg = history[-1]
                        preview = last_msg['content'][:100] + "..." if len(last_msg['content']) > 100 else last_msg['content']
                        st.write(f"💬 Tin nhắn cuối: {preview}")
                        st.write(f"📊 Tổng: {len(history)} tin nhắn")
                
                with col2:
                    if st.button("📂 Tải lại", key=f"load_{i}"):
                        # Load session vào chat hiện tại
                        st.session_state.chat_history = session.get('history', [])
                        st.session_state.current_chat_session_id = session['_id']
                        st.success(f"Đã tải phiên chat: {session.get('session_name')}")
                        st.rerun()
                
                with col3:
                    if st.button("📋 Xem", key=f"view_{i}"):
                        st.session_state[f"viewing_{session['_id']}"] = True
                        st.rerun()
                
                with col4:
                    if st.button("🗑️ Xóa", key=f"delete_session_{i}"):
                        st.session_state[f"confirm_delete_session_{session['_id']}"] = True
                        st.rerun()
                
                # Hiển thị chi tiết session khi nhấn "Xem"
                if st.session_state.get(f"viewing_{session['_id']}", False):
                    with st.expander(f"👁️ Chi tiết: {session.get('session_name')}", expanded=True):
                        st.write(f"**System Prompt:** {session.get('system_prompt', 'N/A')}")
                        st.write("**Lịch sử chat:**")
                        
                        for msg in session.get('history', []):
                            role_icon = "🧑" if msg['role'] == 'user' else "🤖"
                            st.write(f"{role_icon} **{msg['role'].upper()}:**")
                            st.write(msg['content'])
                            st.write("---")
                        
                        if st.button("❌ Đóng", key=f"close_view_{i}"):
                            st.session_state[f"viewing_{session['_id']}"] = False
                            st.rerun()
                
                # Xác nhận xóa session
                if st.session_state.get(f"confirm_delete_session_{session['_id']}", False):
                    st.warning(f"⚠️ Bạn có chắc chắn muốn xóa phiên chat **{session.get('session_name')}**?")
                    col_confirm, col_cancel = st.columns(2)
                    
                    with col_confirm:
                        if st.button("✅ Xác nhận xóa", key=f"confirm_delete_session_yes_{i}"):
                            if delete_chat_session(str(session['_id'])):
                                st.success("Đã xóa phiên chat thành công!")
                                st.session_state[f"confirm_delete_session_{session['_id']}"] = False
                                st.rerun()
                            else:
                                st.error("Lỗi khi xóa phiên chat.")
                    
                    with col_cancel:
                        if st.button("❌ Hủy", key=f"confirm_delete_session_no_{i}"):
                            st.session_state[f"confirm_delete_session_{session['_id']}"] = False
                            st.rerun()
                
                st.divider()

with tab3:
    st.subheader("📊 Xuất dữ liệu & Tóm tắt")
    
    # Chọn session để xuất hoặc tóm tắt
    export_sessions = get_all_chat_sessions()
    
    if not export_sessions:
        st.info("Chưa có phiên chat nào để xuất hoặc tóm tắt.")
    else:
        # Selectbox để chọn session
        session_options = {
            f"{session.get('session_name', 'Phiên chat')} - {session.get('created_at', '').strftime('%d/%m/%Y %H:%M') if isinstance(session.get('created_at'), datetime.datetime) else str(session.get('created_at', ''))}": session['_id'] 
            for session in export_sessions
        }
        session_options["📝 Phiên chat hiện tại"] = "current"
        
        selected_session_key = st.selectbox("Chọn phiên chat:", list(session_options.keys()))
        selected_session_id = session_options[selected_session_key]
        
        # Lấy dữ liệu chat
        if selected_session_id == "current":
            chat_data = st.session_state.chat_history
            session_name = "Phiên chat hiện tại"
        else:
            session_data = get_chat_session(selected_session_id)
            chat_data = session_data.get('history', []) if session_data else []
            session_name = session_data.get('session_name', 'Phiên chat') if session_data else 'Phiên chat'
        
        if not chat_data:
            st.warning("Phiên chat này chưa có nội dung.")
        else:
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("### 📤 Xuất dữ liệu")
                
                # Xuất định dạng Text
                if st.button("📄 Xuất định dạng Text"):
                    text_content = f"=== {session_name} ===\n\n"
                    for msg in chat_data:
                        role_name = "NGƯỜI DÙNG" if msg['role'] == 'user' else "AI"
                        text_content += f"{role_name}:\n{msg['content']}\n\n" + "-"*50 + "\n\n"
                    
                    st.download_button(
                        label="💾 Tải file Text",
                        data=text_content,
                        file_name=f"chat_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                        mime="text/plain"
                    )
                
                # Xuất định dạng JSON
                if st.button("📋 Xuất định dạng JSON"):
                    json_content = {
                        "session_name": session_name,
                        "exported_at": datetime.datetime.now().isoformat(),
                        "chat_history": chat_data
                    }
                    
                    st.download_button(
                        label="💾 Tải file JSON",
                        data=json.dumps(json_content, ensure_ascii=False, indent=2),
                        file_name=f"chat_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )
                
                # Xuất định dạng Markdown
                if st.button("📝 Xuất định dạng Markdown"):
                    md_content = f"# {session_name}\n\n"
                    md_content += f"*Xuất lúc: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}*\n\n"
                    
                    for msg in chat_data:
                        role_icon = "👤" if msg['role'] == 'user' else "🤖"
                        role_name = "Người dùng" if msg['role'] == 'user' else "AI Assistant"
                        md_content += f"## {role_icon} {role_name}\n\n"
                        md_content += f"{msg['content']}\n\n"
                        md_content += "---\n\n"
                    
                    st.download_button(
                        label="💾 Tải file Markdown",
                        data=md_content,
                        file_name=f"chat_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                        mime="text/markdown"
                    )
            
            with col2:
                st.write("### 🔍 Tạo tóm tắt")
                
                if st.button("✨ Tạo tóm tắt nội dung chat"):
                    if len(chat_data) == 0:
                        st.warning("Không có nội dung để tóm tắt.")
                    else:
                        try:
                            # Tạo prompt tóm tắt
                            summary_prompt = "Hãy tóm tắt cuộc trò chuyện sau đây một cách ngắn gọn và súc tích:\n\n"
                            for msg in chat_data:
                                role_name = "Người dùng" if msg['role'] == 'user' else "AI"
                                summary_prompt += f"{role_name}: {msg['content']}\n\n"
                            
                            summary_prompt += "\nTóm tắt:"
                            
                            # Sử dụng LLM hiện tại để tạo tóm tắt
                            llm_provider = get_llm_provider(st.session_state.api_provider, st.session_state.api_key)
                            
                            with st.spinner("Đang tạo tóm tắt..."):
                                summary_response = ""
                                response_stream = llm_provider.chat_stream(
                                    messages=[{"role": "user", "content": summary_prompt}],
                                    model=available_models[0] if available_models else "gpt-3.5-turbo",
                                    temperature=0.3,
                                    max_tokens=1000,
                                    system_prompt="Bạn là một trợ lý AI chuyên tóm tắt nội dung. Hãy tạo ra bản tóm tắt ngắn gọn, đầy đủ và dễ hiểu."
                                )
                                
                                for chunk in response_stream:
                                    summary_response += chunk
                                
                                st.success("✅ Tóm tắt đã được tạo!")
                                st.write("### 📋 Tóm tắt nội dung:")
                                st.write(summary_response)
                                
                                # Nút tải tóm tắt
                                summary_file_content = f"TÓM TẮT CUỘC TRÒ CHUYỆN\n"
                                summary_file_content += f"Phiên: {session_name}\n"
                                summary_file_content += f"Tạo lúc: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n"
                                summary_file_content += "="*50 + "\n\n"
                                summary_file_content += summary_response
                                
                                st.download_button(
                                    label="💾 Tải tóm tắt",
                                    data=summary_file_content,
                                    file_name=f"summary_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                                    mime="text/plain"
                                )
                        
                        except Exception as e:
                            st.error(f"Lỗi khi tạo tóm tắt: {e}")
                
                st.write("### 📈 Thống kê chat")
                st.write(f"**Tổng số tin nhắn:** {len(chat_data)}")
                user_msgs = [msg for msg in chat_data if msg['role'] == 'user']
                ai_msgs = [msg for msg in chat_data if msg['role'] == 'assistant']
                st.write(f"**Tin nhắn người dùng:** {len(user_msgs)}")
                st.write(f"**Tin nhắn AI:** {len(ai_msgs)}")
                
                if chat_data:
                    total_chars = sum(len(msg['content']) for msg in chat_data)
                    st.write(f"**Tổng ký tự:** {total_chars:,}")
                    avg_chars = total_chars / len(chat_data)
                    st.write(f"**Trung bình ký tự/tin:** {avg_chars:.0f}") 