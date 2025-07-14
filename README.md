# AI Tools Platform

Một bộ công cụ AI cá nhân, mạnh mẽ và linh hoạt được xây dựng với Streamlit.

## Các tính năng chính

- **💬 Chat AI**: Trò chuyện trực tiếp với các mô hình AI như GPT, Gemini, Claude, DeepSeek
- **📝 Prompt Manager**: Tạo, lưu trữ và quản lý các System Prompt yêu thích
- **🌐 Translation Tool**: Dịch thuật, tóm tắt và phân tích văn bản chuyên sâu

## Cài đặt

1. **Clone repository**

2. **Tạo môi trường ảo (khuyến nghị):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Trên Windows: venv\Scripts\activate
   ```

3. **Cài đặt dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Cấu hình

Trước khi sử dụng, bạn cần chuẩn bị:

### 1. MongoDB URI
- Tạo tài khoản MongoDB Atlas miễn phí tại [mongodb.com](https://www.mongodb.com/)
- Hoặc sử dụng MongoDB local
- Lấy connection string URI

### 2. API Keys
Tùy thuộc vào nhà cung cấp AI bạn muốn sử dụng:
- **OpenAI**: [platform.openai.com](https://platform.openai.com/)
- **Google Gemini**: [ai.google.dev](https://ai.google.dev/)
- **Anthropic Claude**: [console.anthropic.com](https://console.anthropic.com/)
- **DeepSeek**: [platform.deepseek.com](https://platform.deepseek.com/)

## Chạy ứng dụng

```bash
streamlit run main.py
```

Ứng dụng sẽ mở tại `http://localhost:8501`

## Hướng dẫn sử dụng

1. **Nhập cấu hình**: Mở thanh sidebar và nhập MongoDB URI và API Key
2. **Khám phá Chat AI**: Trò chuyện với AI models khác nhau
3. **Quản lý Prompts**: Tạo và lưu trữ các system prompts tùy chỉnh
4. **Sử dụng Translation Tool**: Dịch và phân tích văn bản (đang phát triển)

## Cấu trúc dự án

```
root/
├── pages/              # Các trang Streamlit
│   ├── 1_💬_Chat_AI.py
│   ├── 2_📝_Prompt_Manager.py
│   └── 3_🌐_Translation_Tool.py
├── utils/              # Utilities và logic core
│   ├── config.py       # Quản lý cấu hình
│   ├── db.py          # Tương tác MongoDB
│   └── llm.py         # Providers cho LLM
├── .streamlit/         # Cấu hình Streamlit
├── requirements.txt    # Dependencies
└── main.py            # Trang chủ
```

## Bảo mật

- Tất cả API keys được mã hóa trong session
- Không lưu trữ credentials cục bộ
- Dữ liệu chỉ được lưu trong MongoDB của bạn

## Phát triển

Để mở rộng platform:
1. Thêm providers mới trong `utils/llm.py`
2. Tạo trang mới trong `pages/`
3. Mở rộng database schema trong `utils/db.py`

## Hỗ trợ

Nếu gặp vấn đề, vui lòng kiểm tra:
- MongoDB connection string
- API keys hợp lệ
- Internet connection
- Dependencies đã được cài đặt đúng 