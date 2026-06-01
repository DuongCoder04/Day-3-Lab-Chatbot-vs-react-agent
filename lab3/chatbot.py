"""
chatbot.py — Baseline Chatbot (không dùng ReAct)
Chỉ 1 LLM call duy nhất. Mục đích: so sánh với agent để thấy hạn chế.

Hạn chế của approach này:
- LLM có thể bịa dữ liệu phòng (hallucination)
- Không kiểm tra availability thực tế
- Không thể xử lý multi-step reasoning
- Không có tool call → không đảm bảo dữ liệu chính xác
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from src.core.llm_provider import LLMProvider
from src.core.gemini_provider import GeminiProvider
from src.core.openai_provider import OpenAIProvider
from src.core.openrouter_provider import OpenRouterProvider
from src.core.local_provider import LocalProvider
from src.telemetry.logger import logger

load_dotenv()

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """Bạn là trợ lý đặt phòng học tại VinUni. Chỉ trả lời ngắn gọn bằng tiếng Việt.

Danh sách phòng:
A101(30 chỗ, projector, whiteboard), A201(50 chỗ, projector, whiteboard, AC),
A301(35 chỗ, projector, whiteboard, AC), B101(20 chỗ, whiteboard),
B205(40 chỗ, projector, whiteboard, AC, lab), B301(60 chỗ, projector, whiteboard, AC, mic),
C102(25 chỗ, whiteboard, AC), C204(80 chỗ, projector, whiteboard, AC, mic, recording),
D101(15 chỗ, whiteboard), D202(45 chỗ, projector, whiteboard, AC, lab)

Quy tắc:
- Chỉ gợi ý phòng trong danh sách trên.
- Ưu tiên phòng có sức chứa vừa đủ.
- Nếu thiếu thông tin (số người, thời gian), hỏi lại.
- KHÔNG bịa thêm thông tin."""


# ---------------------------------------------------------------------------
# Chatbot class
# ---------------------------------------------------------------------------

class ClassroomChatbot:
    def __init__(self, provider: LLMProvider):
        self.provider = provider

    def chat(self, user_message: str) -> str:
        """
        Gửi tin nhắn và nhận gợi ý phòng học.
        Chỉ 1 LLM call duy nhất — không có tool call.
        """
        logger.log_event("CHATBOT_REQUEST", {
            "input": user_message,
            "model": self.provider.model_name
        })

        result = self.provider.generate(
            prompt=user_message,
            system_prompt=SYSTEM_PROMPT
        )

        response = result["content"]

        # Post-processing: cắt nếu model tự thêm prompt mới vào output
        cutoff_markers = ["Phần mới:", "Lưu đọc", "Nhận thức", "User:", "<|"]
        for marker in cutoff_markers:
            if marker in response:
                response = response[:response.index(marker)].strip()

        logger.log_event("CHATBOT_RESPONSE", {
            "output": response,
            "latency_ms": result["latency_ms"],
            "usage": result["usage"]
        })

        return response


# ---------------------------------------------------------------------------
# Factory: tạo provider từ .env
# ---------------------------------------------------------------------------

def create_provider() -> LLMProvider:
    provider_name = os.getenv("DEFAULT_PROVIDER", "openrouter").lower()

    if provider_name == "openai":
        return OpenAIProvider(
            model_name=os.getenv("DEFAULT_MODEL", "gpt-4o"),
            api_key=os.getenv("OPENAI_API_KEY")
        )
    elif provider_name == "google":
        return GeminiProvider(
            model_name=os.getenv("DEFAULT_MODEL", "gemini-1.5-flash"),
            api_key=os.getenv("GEMINI_API_KEY")
        )
    elif provider_name == "openrouter":
        return OpenRouterProvider(
            model_name=os.getenv("OPENROUTER_MODEL", os.getenv("DEFAULT_MODEL", "meta-llama/llama-3.1-8b-instruct:free")),
            api_key=os.getenv("OPENROUTER_API_KEY")
        )
    else:  # local
        model_path = os.getenv("LOCAL_MODEL_PATH", "./models/Phi-3-mini-4k-instruct-q4.gguf")
        return LocalProvider(model_path=model_path)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    provider = create_provider()
    chatbot = ClassroomChatbot(provider)

    print("=== Classroom Chatbot (Baseline) ===")
    print("Gõ 'quit' để thoát.\n")

    while True:
        user_input = input("Bạn: ").strip()
        if user_input.lower() in ("quit", "exit", "q"):
            break
        if not user_input:
            continue

        response = chatbot.chat(user_input)
        print(f"Chatbot: {response}\n")
