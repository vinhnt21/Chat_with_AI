# AI Tools Platform

## Ảnh Nhìn Chung

* 1 trang giao diện Streamlit chính (“Main Screen”), chứa các nút điều hướng đến các tool con
* Mỗi tool là một màn hình con (“page”) tích hợp AI
* Dành cho **cá nhân**, không có đăng nhập: mỗi lần dùng phải nhập API key (OpenAI, MongoDB, ...)

---

## Tech Stack (Free Tier)

* **UI**: Streamlit multipage app
* **Database**: MongoDB Atlas Free Tier

  * Lưu: chat history, system prompts, API usage logs
* **Logic handling**: LangChain
* **API Providers**:

  * OpenAI, Google GenAI, Anthropic, DeepSeek, Gemini

---

## Modules (Tools)

### 1. **System Prompt Manager**

* Chức năng:

  * Tạo prompt mới
  * Chỉnh sửa prompt
  * Xóa prompt
* Lưu trữ trên MongoDB (collection: `system_prompts`)
* Thêm metadata: `created_at`, `used_count`, `tags`

### 2. **Chat AI qua API**

* **Tính năng**:

  * Nhập API key
  * Chọn nhà cung cấp (OpenAI, Google, ...)
  * Chọn model (dựa trên API provider)
  * Nhập system prompt (hoặc chọn từ danh sách prompt đã lưu)
  * Tùy chỉnh temperature, max tokens, top\_p, stop, n, stream...
  * Thinking budget: hiển thị giới hạn tokens / cost
  * Stream text output (nếu hỗ trợ)
  * Lưu lại chat history (MongoDB collection: `chats`)
  * Lưu log lần gọi API (collection: `logs`)

### 3. **Translation Tool**

* **Input**: Văn bản gốc
* **Tùy chọn Output**:

  * Có văn bản dịch
  * Có văn bản tóm tắt
  * Note từ/cụm từ hay và phiên âm
* **Giao diện**:

  * Mỗi output được hiển thị trong một box riêng
  * Cho phép copy / export
* **Logic**: Tích hợp prompt chain với langchain

---

## Góp ý bổ sung:

* Cân nhắc tách riêng lớp config với session state để dễ reuse (API key, config model)
* Cho phép xuất toàn bộ chat/translate ra markdown / txt / JSON

---
