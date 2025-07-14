#!/usr/bin/env python3
"""
Script để test kết nối MongoDB bên ngoài Streamlit
Chạy bằng lệnh: python test_mongodb.py
"""
import sys
from pymongo import MongoClient

def test_mongodb_connection(mongo_uri):
    """Test MongoDB connection với nhiều phương pháp khác nhau"""
    
    print("🔄 Đang test kết nối MongoDB...")
    print(f"URI: {mongo_uri[:20]}...")  # Chỉ hiện một phần URI cho bảo mật
    
    methods = [
        {
            "name": "Phương pháp 1: TLS hiện đại",
            "config": {
                "serverSelectionTimeoutMS": 30000,
                "connectTimeoutMS": 30000,
                "socketTimeoutMS": 30000,
                "tls": True,
                "tlsAllowInvalidCertificates": True,
                "retryWrites": True,
                "w": 'majority'
            }
        },
        {
            "name": "Phương pháp 2: SSL legacy",
            "config": {
                "serverSelectionTimeoutMS": 30000,
                "connectTimeoutMS": 30000,
                "socketTimeoutMS": 30000,
                "ssl": True,
                "ssl_cert_reqs": None,
                "retryWrites": True
            }
        },
        {
            "name": "Phương pháp 3: Cơ bản",
            "config": {
                "serverSelectionTimeoutMS": 30000
            }
        }
    ]
    
    for method in methods:
        print(f"\n📡 {method['name']}...")
        try:
            client = MongoClient(mongo_uri, **method['config'])
            result = client.admin.command('ping')
            print(f"✅ THÀNH CÔNG! Ping result: {result}")
            
            # Test thêm một số operations
            db = client["test_db"]
            collection = db["test_collection"]
            
            # Test insert
            test_doc = {"test": "document", "timestamp": "2024"}
            insert_result = collection.insert_one(test_doc)
            print(f"✅ Insert thành công: {insert_result.inserted_id}")
            
            # Test find
            found_doc = collection.find_one({"_id": insert_result.inserted_id})
            print(f"✅ Find thành công: {found_doc}")
            
            # Cleanup
            collection.delete_one({"_id": insert_result.inserted_id})
            print("✅ Cleanup thành công")
            
            client.close()
            print(f"🎉 {method['name']} HOÀN TOÀN THÀNH CÔNG!")
            return True
            
        except Exception as e:
            print(f"❌ THẤT BẠI: {e}")
    
    print("\n❌ Tất cả phương pháp đều thất bại!")
    return False

if __name__ == "__main__":
    # Nhập MongoDB URI
    if len(sys.argv) > 1:
        mongo_uri = sys.argv[1]
    else:
        mongo_uri = input("Nhập MongoDB URI: ")
    
    if not mongo_uri:
        print("❌ Vui lòng cung cấp MongoDB URI!")
        sys.exit(1)
    
    success = test_mongodb_connection(mongo_uri)
    sys.exit(0 if success else 1) 