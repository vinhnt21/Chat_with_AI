import streamlit as st
from openai import OpenAI
import google.generativeai as genai
import anthropic

class LLMProvider:
    """Lớp cơ sở cho các nhà cung cấp LLM."""
    def __init__(self, api_key):
        if not api_key:
            raise ValueError("API key is required.")
        self.api_key = api_key

    def get_models(self):
        raise NotImplementedError

    def chat_stream(self, messages, model, temperature, max_tokens, system_prompt):
        raise NotImplementedError

class OpenAIProvider(LLMProvider):
    """Triển khai cho OpenAI."""
    def __init__(self, api_key):
        super().__init__(api_key)
        self.client = OpenAI(api_key=self.api_key)

    def get_models(self):
        return ["gpt-4.1-mini","gpt-4.1-nano", "gpt-4o-mini" ]

    def chat_stream(self, messages, model, temperature, max_tokens, system_prompt):
        messages_with_system = [{"role": "system", "content": system_prompt}] + messages
        stream = self.client.chat.completions.create(
            model=model,
            messages=messages_with_system,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True
        )
        for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                yield content

class GoogleProvider(LLMProvider):
    """Triển khai cho Google Gemini."""
    def __init__(self, api_key):
        super().__init__(api_key)
        genai.configure(api_key=self.api_key)

    def get_models(self):
        return ["gemini-2.5-flash", "gemini-2.5-pro"]

    def chat_stream(self, messages, model, temperature, max_tokens, system_prompt):
        generation_config = {
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }
        
        # Configure safety settings to be less restrictive
        safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_ONLY_HIGH"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_ONLY_HIGH"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_ONLY_HIGH"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_ONLY_HIGH"
            },
        ]
        
        gemini_model = genai.GenerativeModel(
            model_name=model,
            generation_config=generation_config,
            safety_settings=safety_settings,
            system_instruction=system_prompt
        )
        # Gemini API xử lý history khác, nó không nhận role 'assistant' trong mảng messages
        # Ta cần chuyển đổi history cho phù hợp
        history_for_gemini = []
        for msg in messages:
            role = 'model' if msg['role'] == 'assistant' else 'user'
            history_for_gemini.append({'role': role, 'parts': [msg['content']]})

        # Lấy tin nhắn cuối cùng của user để stream
        if history_for_gemini and history_for_gemini[-1]['role'] == 'user':
             last_user_message = history_for_gemini.pop()['parts']
             chat_session = gemini_model.start_chat(history=history_for_gemini)
             try:
                 response = chat_session.send_message(last_user_message, stream=True)
                 for chunk in response:
                     if hasattr(chunk, 'text') and chunk.text:
                         yield chunk.text
                     elif hasattr(chunk, 'parts') and chunk.parts:
                         for part in chunk.parts:
                             if hasattr(part, 'text') and part.text:
                                 yield part.text
             except Exception as e:
                 # Handle safety filter blocks and other errors
                 if "finish_reason" in str(e) or "safety" in str(e).lower():
                     yield "⚠️ Nội dung bị chặn bởi bộ lọc an toàn của Gemini. Vui lòng thử lại với văn bản khác hoặc chuyển sang model khác."
                 else:
                     yield f"❌ Lỗi Gemini API: {str(e)}"

class AnthropicProvider(LLMProvider):
    """Triển khai cho Anthropic Claude."""
    def __init__(self, api_key):
        super().__init__(api_key)
        self.client = anthropic.Anthropic(api_key=self.api_key)

    def get_models(self):
        return ["claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"]

    def chat_stream(self, messages, model, temperature, max_tokens, system_prompt):
        with self.client.messages.stream(
            model=model,
            messages=messages,
            system=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens
        ) as stream:
            for text in stream.text_stream:
                yield text

class DeepSeekProvider(LLMProvider):
    """Triển khai cho DeepSeek."""
    def __init__(self, api_key):
        super().__init__(api_key)
        self.client = OpenAI(api_key=self.api_key, base_url="https://api.deepseek.com/v1")

    def get_models(self):
        return ["deepseek-chat", "deepseek-coder"]

    def chat_stream(self, messages, model, temperature, max_tokens, system_prompt):
        messages_with_system = [{"role": "system", "content": system_prompt}] + messages
        stream = self.client.chat.completions.create(
            model=model,
            messages=messages_with_system,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True
        )
        for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                yield content

def get_llm_provider(api_provider, api_key):
    """Factory function để lấy instance của nhà cung cấp LLM."""
    provider_map = {
        "OpenAI": OpenAIProvider,
        "Google": GoogleProvider,
        "Anthropic": AnthropicProvider,
        "DeepSeek": DeepSeekProvider
    }
    provider_class = provider_map.get(api_provider)
    if provider_class:
        return provider_class(api_key)
    else:
        st.error(f"Nhà cung cấp {api_provider} chưa được hỗ trợ.")
        return None 