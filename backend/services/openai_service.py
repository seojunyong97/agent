"""Google Gemini API 호출 서비스"""

import os
import google.generativeai as genai

_model = None


def get_model():
    global _model
    if _model is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY 환경변수가 설정되지 않았습니다.")
        genai.configure(api_key=api_key)
        _model = genai.GenerativeModel("gemini-2.0-flash")
    return _model


def chat_with_context(
    system_prompt: str,
    messages: list[dict],
    user_message: str,
) -> str:
    """
    시스템 프롬프트 + 이전 대화 + 새 메시지로 Gemini 호출.
    반환: AI 응답 텍스트
    """
    model = get_model()

    # Gemini 형식으로 대화 히스토리 변환
    history = []
    for msg in messages:
        role = "user" if msg["role"] == "user" else "model"
        history.append({"role": role, "parts": [msg["content"]]})

    chat = model.start_chat(history=history)

    # 시스템 프롬프트를 첫 메시지에 포함
    full_message = f"[시스템 지시]\n{system_prompt}\n\n[사용자 질문]\n{user_message}"

    # 히스토리가 있으면 시스템 프롬프트 없이 질문만
    if history:
        full_message = user_message

    response = chat.send_message(full_message)
    return response.text
