"""대화 기록 API 라우터"""

from fastapi import APIRouter, HTTPException
from models.schemas import ConversationCreate, ConversationResponse, MessageItem
from services.firebase import get_db
from datetime import datetime

router = APIRouter(prefix="/api/conversations", tags=["대화 기록"])


@router.post("", response_model=dict, status_code=201)
async def create_conversation(conv: ConversationCreate):
    """새 대화 저장"""
    db = get_db()
    doc_ref = db.collection("conversations").document()
    doc_data = {
        "title": conv.title,
        "messages": [m.model_dump() for m in conv.messages],
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }
    doc_ref.set(doc_data)
    return {"id": doc_ref.id, "title": conv.title, "created_at": doc_data["created_at"]}


@router.get("")
async def get_conversations():
    """대화 목록 조회 (messages 제외, 가벼운 목록)"""
    db = get_db()
    docs = db.collection("conversations").order_by("created_at", direction="DESCENDING").stream()
    result = []
    for doc in docs:
        d = doc.to_dict()
        messages = d.get("messages", [])
        result.append({
            "id": doc.id,
            "title": d.get("title", "제목 없음"),
            "created_at": d.get("created_at", ""),
            "message_count": len(messages),
            "preview": messages[-1]["content"][:50] if messages else "",
        })
    return result


@router.get("/{conv_id}")
async def get_conversation(conv_id: str):
    """특정 대화의 전체 messages 조회"""
    db = get_db()
    doc = db.collection("conversations").document(conv_id).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="대화를 찾을 수 없습니다.")
    d = doc.to_dict()
    return {
        "id": doc.id,
        "title": d.get("title", ""),
        "messages": d.get("messages", []),
        "created_at": d.get("created_at", ""),
    }


@router.delete("/{conv_id}")
async def delete_conversation(conv_id: str):
    """대화 삭제"""
    db = get_db()
    doc_ref = db.collection("conversations").document(conv_id)
    doc = doc_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="대화를 찾을 수 없습니다.")
    doc_ref.delete()
    return {"message": "대화 삭제 완료", "id": conv_id}
