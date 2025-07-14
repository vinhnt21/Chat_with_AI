import streamlit as st
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure
from bson import ObjectId
import datetime

@st.cache_resource
def get_db_client(mongo_uri):
    """Kết nối tới MongoDB và trả về client. Cache resource để tránh kết nối lại."""
    try:
        # Thử phương pháp kết nối chính (với TLS configuration hiện đại)
        client = MongoClient(
            mongo_uri, 
            serverSelectionTimeoutMS=30000,  # Tăng timeout
            connectTimeoutMS=30000,
            socketTimeoutMS=30000,
            tls=True,  # Sử dụng tls thay vì ssl
            tlsAllowInvalidCertificates=True,  # Cho phép certificate không hợp lệ
            retryWrites=True,  # Cho phép retry writes
            w='majority'  # Write concern
        )
        client.admin.command('ping')
        st.success("✅ Kết nối MongoDB thành công!")
        return client
    except Exception as e:
        st.warning(f"⚠️ Phương pháp kết nối chính thất bại: {e}")
        
        # Thử phương pháp kết nối thay thế 1 (với SSL legacy)
        try:
            client = MongoClient(
                mongo_uri,
                serverSelectionTimeoutMS=30000,
                connectTimeoutMS=30000,
                socketTimeoutMS=30000,
                ssl=True,  # Sử dụng SSL legacy
                ssl_cert_reqs=None,  # Không yêu cầu certificate
                retryWrites=True
            )
            client.admin.command('ping')
            st.success("✅ Kết nối MongoDB thành công (phương pháp thay thế 1)!")
            return client
        except Exception as e2:
            st.warning(f"⚠️ Phương pháp kết nối thay thế 1 thất bại: {e2}")
            
            # Thử phương pháp kết nối thay thế 2 (cơ bản nhất)
            try:
                client = MongoClient(
                    mongo_uri,
                    serverSelectionTimeoutMS=30000
                )
                client.admin.command('ping')
                st.success("✅ Kết nối MongoDB thành công (phương pháp thay thế 2)!")
                return client
            except Exception as e3:
                st.error(f"❌ Tất cả phương pháp kết nối đều thất bại:")
                st.error(f"Lỗi chính: {e}")
                st.error(f"Lỗi thay thế 1: {e2}")
                st.error(f"Lỗi thay thế 2: {e3}")
                st.info("💡 Gợi ý: Kiểm tra lại MongoDB URI và đảm bảo rằng cluster đang hoạt động.")
                return None

def get_database_name():
    """Lấy tên database dựa trên user group."""
    user_group = st.session_state.get("user_group")
    if user_group == "ADMIN":
        return "ai_tools_admin_db"
    elif user_group == "GUEST":
        return "ai_tools_guest_db"
    else:
        return "ai_tools_default_db"  # fallback

def get_collection(collection_name):
    """Lấy một collection từ database tương ứng với user group."""
    if st.session_state.get("mongo_uri"):
        if "db_client" not in st.session_state or st.session_state.db_client is None:
            st.session_state.db_client = get_db_client(st.session_state.mongo_uri)
        if st.session_state.db_client:
            # Sử dụng database riêng cho từng user group
            db_name = get_database_name()
            db = st.session_state.db_client[db_name]
            collection = db[collection_name]
            return collection
    return None

# --- Prompts Collection Functions ---

def get_all_prompts():
    """Lấy tất cả prompts từ DB của user hiện tại."""
    prompts_coll = get_collection("system_prompts")
    if prompts_coll is not None:
        return list(prompts_coll.find())
    return []

def save_prompt(name, content, tags):
    """Lưu một prompt mới hoặc cập nhật prompt đã có cho user hiện tại."""
    prompts_coll = get_collection("system_prompts")
    if prompts_coll is not None:
        doc = {
            "name": name,
            "content": content,
            "tags": tags,
            "user_group": st.session_state.get("user_group"),  # Thêm user_group để phân biệt
            "created_at": datetime.datetime.now(datetime.timezone.utc),
            "last_used": None,
            "used_count": 0
        }
        prompts_coll.insert_one(doc)
        return True
    return False

def update_prompt(prompt_id, data):
    """Cập nhật một prompt của user hiện tại."""
    prompts_coll = get_collection("system_prompts")
    if prompts_coll is not None:
        # Thêm user_group filter để đảm bảo chỉ update prompt của user hiện tại
        filter_query = {
            "_id": ObjectId(prompt_id),
            "user_group": st.session_state.get("user_group")
        }
        prompts_coll.update_one(filter_query, {"$set": data})
        return True
    return False

def delete_prompt(prompt_id):
    """Xóa một prompt của user hiện tại."""
    prompts_coll = get_collection("system_prompts")
    if prompts_coll is not None:
        # Thêm user_group filter để đảm bảo chỉ xóa prompt của user hiện tại
        filter_query = {
            "_id": ObjectId(prompt_id),
            "user_group": st.session_state.get("user_group")
        }
        prompts_coll.delete_one(filter_query)
        return True
    return False

# --- Chat Sessions Collection Functions ---

def get_all_chat_sessions():
    """Lấy tất cả phiên chat từ DB của user hiện tại, sắp xếp theo thời gian mới nhất."""
    chat_coll = get_collection("chat_sessions")
    if chat_coll is not None:
        # Filter theo user_group
        filter_query = {"user_group": st.session_state.get("user_group")}
        return list(chat_coll.find(filter_query).sort("updated_at", -1))
    return []

def get_chat_session(session_id):
    """Lấy một phiên chat cụ thể theo ID của user hiện tại."""
    chat_coll = get_collection("chat_sessions")
    if chat_coll is not None:
        # Thêm user_group filter
        filter_query = {
            "_id": ObjectId(session_id),
            "user_group": st.session_state.get("user_group")
        }
        return chat_coll.find_one(filter_query)
    return None

def delete_chat_session(session_id):
    """Xóa một phiên chat của user hiện tại."""
    chat_coll = get_collection("chat_sessions")
    if chat_coll is not None:
        # Thêm user_group filter
        filter_query = {
            "_id": ObjectId(session_id),
            "user_group": st.session_state.get("user_group")
        }
        chat_coll.delete_one(filter_query)
        return True
    return False

def save_chat_session(session_data):
    """Lưu một phiên chat vào DB của user hiện tại."""
    chat_coll = get_collection("chat_sessions")
    if chat_coll is not None:
        session_data["updated_at"] = datetime.datetime.now(datetime.timezone.utc)
        session_data["user_group"] = st.session_state.get("user_group")  # Thêm user_group
        
        if "_id" in session_data and session_data["_id"] is not None:
            # Update existing session - thêm user_group filter
            filter_query = {
                "_id": session_data["_id"],
                "user_group": st.session_state.get("user_group")
            }
            chat_coll.update_one(filter_query, {"$set": session_data})
            return session_data["_id"]
        else:
            # Create new session
            session_data.pop("_id", None)
            session_data["created_at"] = datetime.datetime.now(datetime.timezone.utc)
            result = chat_coll.insert_one(session_data)
            return result.inserted_id
    return None 