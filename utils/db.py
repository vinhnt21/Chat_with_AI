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

def get_collection(collection_name):
    """Lấy một collection từ database, nếu chưa có db_client, thì tạo db_client
    Nếu có db_client, thì lấy collection từ db_client
    Nếu không có collection, thì tạo collection
    """
    # if st.session_state.get("mongo_uri"):
    #     if "db_client" not in st.session_state or st.session_state.db_client is None:
    #         st.session_state.db_client = get_db_client(st.session_state.mongo_uri)

    #     if st.session_state.db_client:
    #         db = st.session_state.db_client["ai_tools_db"]
    #         return db[collection_name]
    # return None
    if st.session_state.get("mongo_uri"):
        if "db_client" not in st.session_state or st.session_state.db_client is None:
            st.session_state.db_client = get_db_client(st.session_state.mongo_uri)
        if st.session_state.db_client:
            db = st.session_state.db_client["ai_tools_db"]
            collection = db[collection_name]
            return collection
    return None

# --- Prompts Collection Functions ---

def get_all_prompts():
    """Lấy tất cả prompts từ DB."""
    prompts_coll = get_collection("prompts")
    if prompts_coll is not None:
        return list(prompts_coll.find())
    return []

def save_prompt(name, content, tags):
    """Lưu một prompt mới hoặc cập nhật prompt đã có."""
    prompts_coll = get_collection("prompts")
    if prompts_coll is not None:
        doc = {
            "name": name,
            "content": content,
            "tags": tags,
            "created_at": datetime.datetime.now(datetime.timezone.utc),
            "last_used": None,
            "used_count": 0
        }
        prompts_coll.insert_one(doc)
        return True
    return False

def update_prompt(prompt_id, data):
    """Cập nhật một prompt."""
    prompts_coll = get_collection("prompts")
    if prompts_coll is not None:
        prompts_coll.update_one({"_id": ObjectId(prompt_id)}, {"$set": data})
        return True
    return False

def delete_prompt(prompt_id):
    """Xóa một prompt."""
    prompts_coll = get_collection("prompts")
    if prompts_coll is not None:
        prompts_coll.delete_one({"_id": ObjectId(prompt_id)})
        return True
    return False

# --- Chat Sessions Collection Functions ---

def save_chat_session(session_data):
    """Lưu một phiên chat vào DB."""
    chat_coll = get_collection("chat_sessions")
    if chat_coll is not None:
        session_data["updated_at"] = datetime.datetime.now(datetime.timezone.utc)
        if "_id" in session_data and session_data["_id"] is not None:
            chat_coll.update_one({"_id": session_data["_id"]}, {"$set": session_data})
            return session_data["_id"]
        else:
            session_data.pop("_id", None)
            session_data["created_at"] = datetime.datetime.now(datetime.timezone.utc)
            result = chat_coll.insert_one(session_data)
            return result.inserted_id
    return None 