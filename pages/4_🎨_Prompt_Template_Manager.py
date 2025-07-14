import streamlit as st
import pandas as pd
import re
from datetime import datetime
from utils.config import initialize_session_state, setup_sidebar, check_configuration
from utils.db import get_collection
from bson import ObjectId

# --- Cấu hình trang ---
st.set_page_config(page_title="Prompt Template Manager", layout="wide")
initialize_session_state()
setup_sidebar()
check_configuration()

st.title("🎨 Quản lý Prompt Template")
st.write("Tạo, quản lý và render các prompt template với biến động.")

# --- Hàm database cho templates ---
def get_all_templates():
    """Lấy tất cả prompt templates từ DB."""
    templates_coll = get_collection("prompt_templates")
    if templates_coll is not None:
        return list(templates_coll.find().sort("created_at", -1))
    return []

def save_template(name, template_content, variables, description=""):
    """Lưu một template mới."""
    templates_coll = get_collection("prompt_templates")
    if templates_coll is not None:
        doc = {
            "name": name,
            "template_content": template_content,
            "variables": variables,
            "description": description,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "used_count": 0
        }
        result = templates_coll.insert_one(doc)
        return result.inserted_id
    return None

def update_template(template_id, data):
    """Cập nhật một template."""
    templates_coll = get_collection("prompt_templates")
    if templates_coll is not None:
        data["updated_at"] = datetime.now()
        templates_coll.update_one({"_id": ObjectId(template_id)}, {"$set": data})
        return True
    return False

def delete_template(template_id):
    """Xóa một template."""
    templates_coll = get_collection("prompt_templates")
    if templates_coll is not None:
        templates_coll.delete_one({"_id": ObjectId(template_id)})
        return True
    return False

def increment_usage_count(template_id):
    """Tăng số lần sử dụng template."""
    templates_coll = get_collection("prompt_templates")
    if templates_coll is not None:
        templates_coll.update_one(
            {"_id": ObjectId(template_id)}, 
            {"$inc": {"used_count": 1}}
        )

# --- Hàm tiện ích ---
def extract_variables(template_content):
    """Trích xuất các biến từ template content (định dạng {variable_name})."""
    variables = re.findall(r'\{([^}]+)\}', template_content)
    return list(set(variables))  # Loại bỏ trùng lặp

def render_template(template_content, variable_values):
    """Render template với các giá trị biến được cung cấp."""
    rendered = template_content
    for var_name, var_value in variable_values.items():
        rendered = rendered.replace(f"{{{var_name}}}", str(var_value))
    return rendered

def validate_template(template_content, variables):
    """Kiểm tra tính hợp lệ của template."""
    extracted_vars = extract_variables(template_content)
    defined_vars = [var['name'] for var in variables]
    
    missing_vars = set(extracted_vars) - set(defined_vars)
    extra_vars = set(defined_vars) - set(extracted_vars)
    
    return missing_vars, extra_vars

# --- Tab chính ---
tab1, tab2, tab3 = st.tabs(["📋 Quản lý Templates", "➕ Tạo Template Mới", "🎯 Render Template"])

# --- Tab: Tạo template mới ---
with tab2:
    st.subheader("Tạo Template Mới")
    st.info("💡 Sử dụng cú pháp {variable_name} để định nghĩa biến trong template.")
    
    # Form input ngoài form để có thể detect biến real-time
    template_name = st.text_input("Tên template:", placeholder="VD: Email Marketing Template")
    template_desc = st.text_area("Mô tả (tùy chọn):", height=100, placeholder="Mô tả ngắn gọn về template này...")
    
    template_content = st.text_area(
        "Nội dung template:", 
        height=200,
        placeholder="VD: Xin chào {customer_name}, bạn có quan tâm đến {product_name} không? Giá chỉ {price} VND.",
        help="Sử dụng {variable_name} để định nghĩa biến"
    )
    
    # Tự động phát hiện biến real-time
    detected_vars = []
    if template_content:
        detected_vars = extract_variables(template_content)
        
        # Cập nhật detected vars vào session state để theo dõi
        if "current_detected_vars" not in st.session_state:
            st.session_state.current_detected_vars = []
        st.session_state.current_detected_vars = detected_vars
        
        if detected_vars:
            st.write("🔍 **Biến được phát hiện:**", ", ".join([f"`{{{var}}}`" for var in detected_vars]))
            
            st.write("**Định nghĩa các biến:**")
            with st.form("variables_form"):
                variables = []
                for var in detected_vars:
                    col1, col2, col3 = st.columns([2, 2, 3])
                    with col1:
                        st.write(f"**{var}**")
                    with col2:
                        var_type = st.selectbox(
                            "Loại", 
                            ["text", "number", "textarea", "date"],
                            key=f"type_{var}",
                            help="Loại input để nhập giá trị cho biến này"
                        )
                    with col3:
                        var_desc = st.text_input(
                            "Mô tả", 
                            key=f"desc_{var}",
                            placeholder=f"Mô tả cho biến {var} (tùy chọn)",
                            help="Mô tả chi tiết cho biến này (có thể để trống)"
                        )
                    
                    variables.append({
                        "name": var,
                        "type": var_type,
                        "description": var_desc
                    })
                
                # Lưu variables vào session state khi form được submit
                submitted = st.form_submit_button("💾 Lưu Template", type="primary")
                if submitted:
                    st.session_state.template_variables = variables
        else:
            # Nếu không có biến, hiển thị nút lưu đơn giản
            submitted = st.button("💾 Lưu Template", type="primary")
            if submitted:
                st.session_state.template_variables = []
    else:
        submitted = st.button("💾 Lưu Template", type="primary")
        if submitted:
            st.session_state.template_variables = []
        
    if submitted:
        if not template_name or not template_content:
            st.error("Tên template và nội dung không được để trống!")
        else:
            # Lấy variables từ session state
            template_variables = st.session_state.get('template_variables', [])
            current_detected_vars = extract_variables(template_content)
            
            # Kiểm tra nếu có biến được định nghĩa
            if current_detected_vars and template_variables:
                # Save template (không cần kiểm tra mô tả nữa, cho phép trống)
                result = save_template(template_name, template_content, template_variables, template_desc)
                if result:
                    st.success("✅ Template đã được lưu thành công!")
                    # Clear session state
                    if 'template_variables' in st.session_state:
                        del st.session_state.template_variables
                    if 'current_detected_vars' in st.session_state:
                        del st.session_state.current_detected_vars
                    st.rerun()
                else:
                    st.error("❌ Có lỗi xảy ra khi lưu template.")
            
            elif current_detected_vars and not template_variables:
                st.error("❌ Vui lòng định nghĩa các biến được phát hiện trong template trước khi lưu!")
            
            elif not current_detected_vars:
                # Save template without variables
                result = save_template(template_name, template_content, [], template_desc)
                if result:
                    st.success("✅ Template đã được lưu thành công!")
                    # Clear session state
                    if 'template_variables' in st.session_state:
                        del st.session_state.template_variables
                    if 'current_detected_vars' in st.session_state:
                        del st.session_state.current_detected_vars
                    st.rerun()
                else:
                    st.error("❌ Có lỗi xảy ra khi lưu template.")
            
            else:
                # Save template
                result = save_template(template_name, template_content, template_variables, template_desc)
                if result:
                    st.success("✅ Template đã được lưu thành công!")
                    # Clear session state
                    if 'template_variables' in st.session_state:
                        del st.session_state.template_variables
                    if 'current_detected_vars' in st.session_state:
                        del st.session_state.current_detected_vars
                    st.rerun()
                else:
                    st.error("❌ Có lỗi xảy ra khi lưu template.")

# --- Tab: Quản lý templates ---
with tab1:
    st.subheader("Danh sách Templates")
    
    templates = get_all_templates()
    
    if not templates:
        st.info("📝 Chưa có template nào. Hãy tạo template đầu tiên ở tab 'Tạo Template Mới'!")
    else:
        # Bộ lọc và tìm kiếm
        col1, col2 = st.columns([3, 1])
        with col1:
            search_term = st.text_input("🔍 Tìm kiếm template:", placeholder="Nhập tên hoặc mô tả...")
        with col2:
            sort_by = st.selectbox("Sắp xếp theo:", ["Mới nhất", "Tên A-Z", "Sử dụng nhiều nhất"])
        
        # Lọc templates
        filtered_templates = templates
        if search_term:
            filtered_templates = [
                t for t in templates 
                if search_term.lower() in t['name'].lower() or 
                   search_term.lower() in t.get('description', '').lower()
            ]
        
        # Sắp xếp
        if sort_by == "Tên A-Z":
            filtered_templates.sort(key=lambda x: x['name'].lower())
        elif sort_by == "Sử dụng nhiều nhất":
            filtered_templates.sort(key=lambda x: x.get('used_count', 0), reverse=True)
        
        # Hiển thị templates
        for i, template in enumerate(filtered_templates):
            with st.container():
                # Header
                col1, col2, col3, col4 = st.columns([4, 1, 1, 1])
                
                with col1:
                    st.markdown(f"### 📄 {template['name']}")
                    if template.get('description'):
                        st.write(template['description'])
                    
                    # Thông tin meta
                    variables_count = len(template.get('variables', []))
                    usage_count = template.get('used_count', 0)
                    created_date = template['created_at'].strftime("%d/%m/%Y")
                    
                    st.caption(f"🔧 {variables_count} biến • 📊 Đã dùng {usage_count} lần • 📅 Tạo {created_date}")
                
                with col2:
                    if st.button("👁️ Xem", key=f"view_{i}"):
                        st.session_state[f"viewing_{template['_id']}"] = True
                        st.rerun()
                
                with col3:
                    if st.button("✏️ Sửa", key=f"edit_{i}"):
                        st.session_state[f"editing_{template['_id']}"] = True
                        st.rerun()
                
                with col4:
                    if st.button("🗑️ Xóa", key=f"delete_{i}"):
                        st.session_state[f"confirm_delete_{template['_id']}"] = True
                        st.rerun()
                
                # Xem template
                if st.session_state.get(f"viewing_{template['_id']}", False):
                    with st.expander("👁️ Chi tiết Template", expanded=True):
                        st.write("**Nội dung template:**")
                        st.code(template['template_content'], language="text")
                        
                        if template.get('variables'):
                            st.write("**Biến:**")
                            for var in template['variables']:
                                st.write(f"• `{{{var['name']}}}` ({var['type']}): {'**Chưa có mô tả**' if not var['description'] else var['description']}")
                        
                        if st.button("✖️ Đóng", key=f"close_view_{i}"):
                            st.session_state[f"viewing_{template['_id']}"] = False
                            st.rerun()
                
                # Form sửa template
                if st.session_state.get(f"editing_{template['_id']}", False):
                    with st.expander("✏️ Chỉnh sửa Template", expanded=True):
                        # Input fields ngoài form để detect biến real-time
                        edit_name = st.text_input("Tên:", value=template['name'], key=f"edit_name_{template['_id']}")
                        edit_desc = st.text_area("Mô tả:", value=template.get('description', ''), height=100, key=f"edit_desc_{template['_id']}")
                        edit_content = st.text_area("Nội dung:", value=template['template_content'], height=200, key=f"edit_content_{template['_id']}")
                        
                        # Detect variables real-time
                        detected_vars = extract_variables(edit_content) if edit_content else []
                        
                        if detected_vars:
                            st.write("🔍 **Biến được phát hiện:**", ", ".join([f"`{{{var}}}`" for var in detected_vars]))
                            
                            st.write("**Chỉnh sửa thông tin biến:**")
                            
                            with st.form(f"edit_variables_form_{template['_id']}"):
                                edit_variables = []
                                for var in detected_vars:
                                    # Tìm thông tin biến cũ nếu có
                                    existing_var = next((v for v in template.get('variables', []) if v['name'] == var), None)
                                    default_type = existing_var['type'] if existing_var else "text"
                                    default_desc = existing_var['description'] if existing_var else ""
                                    
                                    col1, col2, col3 = st.columns([2, 2, 3])
                                    with col1:
                                        st.write(f"**{var}**")
                                    with col2:
                                        var_type = st.selectbox(
                                            "Loại", 
                                            ["text", "number", "textarea", "date"],
                                            index=["text", "number", "textarea", "date"].index(default_type),
                                            key=f"edit_type_{template['_id']}_{var}",
                                            help="Loại input để nhập giá trị cho biến này"
                                        )
                                    with col3:
                                        var_desc = st.text_input(
                                            "Mô tả", 
                                            value=default_desc,
                                            key=f"edit_desc_var_{template['_id']}_{var}",
                                            placeholder=f"Mô tả cho biến {var}",
                                            help="Mô tả chi tiết cho biến này (có thể để trống)"
                                        )
                                    
                                    edit_variables.append({
                                        "name": var,
                                        "type": var_type,
                                        "description": var_desc
                                    })
                                
                                col_save, col_cancel = st.columns(2)
                                with col_save:
                                    if st.form_submit_button("💾 Lưu"):
                                        update_data = {
                                            "name": edit_name,
                                            "description": edit_desc,
                                            "template_content": edit_content,
                                            "variables": edit_variables
                                        }
                                        
                                        if update_template(str(template['_id']), update_data):
                                            st.success("✅ Template đã được cập nhật!")
                                            st.session_state[f"editing_{template['_id']}"] = False
                                            st.rerun()
                                        else:
                                            st.error("❌ Có lỗi xảy ra khi cập nhật.")
                                
                                with col_cancel:
                                    if st.form_submit_button("❌ Hủy"):
                                        st.session_state[f"editing_{template['_id']}"] = False
                                        st.rerun()
                        else:
                            # Không có biến, chỉ cần lưu thông tin cơ bản
                            col_save, col_cancel = st.columns(2)
                            with col_save:
                                if st.button("💾 Lưu", key=f"save_no_vars_{template['_id']}"):
                                    update_data = {
                                        "name": edit_name,
                                        "description": edit_desc,
                                        "template_content": edit_content,
                                        "variables": []
                                    }
                                    
                                    if update_template(str(template['_id']), update_data):
                                        st.success("✅ Template đã được cập nhật!")
                                        st.session_state[f"editing_{template['_id']}"] = False
                                        st.rerun()
                                    else:
                                        st.error("❌ Có lỗi xảy ra khi cập nhật.")
                            
                            with col_cancel:
                                if st.button("❌ Hủy", key=f"cancel_no_vars_{template['_id']}"):
                                    st.session_state[f"editing_{template['_id']}"] = False
                                    st.rerun()
                
                # Xác nhận xóa
                if st.session_state.get(f"confirm_delete_{template['_id']}", False):
                    st.warning(f"⚠️ Bạn có chắc chắn muốn xóa template **{template['name']}**?")
                    col_yes, col_no = st.columns(2)
                    
                    with col_yes:
                        if st.button("✅ Xóa", key=f"confirm_yes_{i}"):
                            if delete_template(str(template['_id'])):
                                st.success("✅ Template đã được xóa!")
                                st.session_state[f"confirm_delete_{template['_id']}"] = False
                                st.rerun()
                            else:
                                st.error("❌ Có lỗi xảy ra khi xóa.")
                    
                    with col_no:
                        if st.button("❌ Hủy", key=f"confirm_no_{i}"):
                            st.session_state[f"confirm_delete_{template['_id']}"] = False
                            st.rerun()
                
                st.divider()

# --- Tab: Render template ---
with tab3:
    st.subheader("🎯 Render Template")
    st.write("Chọn một template và điền các biến để tạo prompt hoàn chỉnh.")
    
    templates = get_all_templates()
    
    if not templates:
        st.info("📝 Không có template nào để render. Hãy tạo template trước!")
    else:
        # Chọn template
        template_options = {f"{t['name']} ({len(t.get('variables', []))} biến)": str(t['_id']) for t in templates}
        selected_template_name = st.selectbox("Chọn template:", list(template_options.keys()))
        
        if selected_template_name:
            selected_template_id = template_options[selected_template_name]
            selected_template = next(t for t in templates if str(t['_id']) == selected_template_id)
            
            # Hiển thị template gốc
            with st.expander("📄 Template gốc", expanded=False):
                st.code(selected_template['template_content'], language="text")
            
            # Form điền biến
            st.write("**Điền giá trị cho các biến:**")
            
            variable_values = {}
            if selected_template.get('variables'):
                with st.form("render_form"):
                    for var in selected_template['variables']:
                        var_name = var['name']
                        var_type = var['type']
                        var_desc = var['description']
                        
                        st.write(f"**{var_name}** - {var_desc}")
                        
                        if var_type == "text":
                            value = st.text_input(f"Giá trị cho {var_name}:", key=f"var_{var_name}")
                        elif var_type == "textarea":
                            value = st.text_area(f"Giá trị cho {var_name}:", key=f"var_{var_name}", height=100)
                        elif var_type == "number":
                            value = st.number_input(f"Giá trị cho {var_name}:", key=f"var_{var_name}")
                        elif var_type == "date":
                            value = st.date_input(f"Giá trị cho {var_name}:", key=f"var_{var_name}")
                            value = value.strftime("%d/%m/%Y") if value else ""
                        else:
                            value = st.text_input(f"Giá trị cho {var_name}:", key=f"var_{var_name}")
                        
                        variable_values[var_name] = value
                    
                    if st.form_submit_button("🎯 Render Template", type="primary"):
                        # Kiểm tra tất cả biến đã được điền
                        missing_vars = [var['name'] for var in selected_template['variables'] if not variable_values.get(var['name'])]
                        
                        if missing_vars:
                            st.error(f"❌ Vui lòng điền đầy đủ các biến: {', '.join(missing_vars)}")
                        else:
                            # Render template
                            rendered_prompt = render_template(selected_template['template_content'], variable_values)
                            
                            # Hiển thị kết quả
                            st.success("✅ Template đã được render thành công!")
                            
                            # Raw text với nút copy
                            st.write("**📄 Raw Text (có thể copy):**")
                            st.code(rendered_prompt, language="text")
                            
                            # Preview formatted
                            st.write("**🎨 Preview:**")
                            st.markdown("---")
                            st.markdown(rendered_prompt)
                            st.markdown("---")
                            
                            # Tăng số lần sử dụng
                            increment_usage_count(selected_template_id)
                            
                            # Lưu vào session state để có thể sử dụng ở tab khác
                            st.session_state['last_rendered_prompt'] = rendered_prompt
                            
                            st.info("💡 Bạn có thể copy text từ khung Raw Text phía trên để sử dụng!")
            
            else:
                st.info("🔧 Template này không có biến nào để điền.")
                
                # Render luôn nếu không có biến
                if st.button("🎯 Hiển thị Template"):
                    # Raw text với nút copy
                    st.write("**📄 Raw Text (có thể copy):**")
                    st.code(selected_template['template_content'], language="text")
                    
                    # Preview formatted
                    st.write("**🎨 Preview:**")
                    st.markdown("---")
                    st.markdown(selected_template['template_content'])
                    st.markdown("---")
                    
                    # Lưu vào session state
                    st.session_state['last_rendered_prompt'] = selected_template['template_content']
                    
                    st.info("💡 Bạn có thể copy text từ khung Raw Text phía trên để sử dụng!")

# Hiển thị prompt đã render gần đây
if st.session_state.get('last_rendered_prompt'):
    with st.sidebar:
        st.markdown("---")
        st.write("**🎯 Prompt gần đây:**")
        with st.expander("Xem prompt", expanded=False):
            st.text_area("", value=st.session_state['last_rendered_prompt'], height=150, disabled=True) 