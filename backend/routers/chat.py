"""AI 챗봇 API — 컨텍스트 주입 방식"""

from fastapi import APIRouter, HTTPException
from models.schemas import ChatRequest, ChatResponse
from services.firebase import get_db
from services.openai_service import chat_with_context
from datetime import datetime

router = APIRouter(prefix="/api/chat", tags=["AI 채팅"])

SYSTEM_PROMPT_TEMPLATE = """당신은 비트코인 데이터 분석 비서입니다.
사용자의 비트코인 가격 데이터를 기반으로 맞춤형 답변을 제공합니다.
친근하고 전문적인 한국어로 답변하세요.

[사용자 데이터 요약]
- 데이터 유형: {data_type}
- 데이터 기간: {period}
- 총 레코드: {count}개
- 평균 가격: ${average:,.2f}
- 최고 가격: ${max:,.2f}
- 최저 가격: ${min:,.2f}
- 최근 트렌드: {trend}

위 데이터를 기반으로 사용자의 질문에 맞춤형 답변을 제공하세요.
수치를 언급할 때는 구체적으로 답변하고, 투자 조언은 삼가되 데이터 분석 인사이트는 제공하세요."""


def _build_system_prompt(summary: dict) -> str:
    """데이터 요약을 시스템 프롬프트에 주입"""
    metrics = summary.get("metrics", {})
    return SYSTEM_PROMPT_TEMPLATE.format(
        data_type=summary.get("data_type", "시계열 데이터"),
        period=summary.get("period", "정보 없음"),
        count=summary.get("count", 0),
        average=metrics.get("average", 0),
        max=metrics.get("max", 0),
        min=metrics.get("min", 0),
        trend=summary.get("trend", "정보 없음"),
    )


@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """
    AI 대화 API
    1. 데이터 요약 조회
    2. 시스템 프롬프트에 주입
    3. GPT API 호출
    4. 대화를 Firestore에 자동 저장
    """
    db = get_db()

    # 1) 데이터 요약 가져오기
    from routers.data import get_data_summary
    summary = await get_data_summary()

    # 2) 시스템 프롬프트 구성
    system_prompt = _build_system_prompt(summary)

    # 3) 기존 대화가 있으면 불러오기
    previous_messages = []
    conv_id = req.conversation_id

    if conv_id:
        conv_doc = db.collection("conversations").document(conv_id).get()
        if conv_doc.exists:
            previous_messages = conv_doc.to_dict().get("messages", [])

    # 4) GPT 호출
    try:
        reply = chat_with_context(system_prompt, previous_messages, req.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI 응답 생성 실패: {str(e)}")

    # 5) 대화 저장 (자동)
    new_messages = previous_messages + [
        {"role": "user", "content": req.message},
        {"role": "assistant", "content": reply},
    ]

    if conv_id:
        # 기존 대화 업데이트
        db.collection("conversations").document(conv_id).update({
            "messages": new_messages,
            "updated_at": datetime.utcnow().isoformat(),
        })
    else:
        # 새 대화 생성
        title = req.message[:30] + ("..." if len(req.message) > 30 else "")
        doc_ref = db.collection("conversations").document()
        doc_ref.set({
            "title": title,
            "messages": new_messages,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        })
        conv_id = doc_ref.id

    return ChatResponse(reply=reply, conversation_id=conv_id)
