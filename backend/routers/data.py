"""데이터 CRUD + 요약 API 라우터"""

from fastapi import APIRouter, HTTPException
from models.schemas import DataCreate, DataUpdate, DataResponse
from services.firebase import get_db
from datetime import datetime

router = APIRouter(prefix="/api/data", tags=["데이터 관리"])


@router.post("", response_model=DataResponse, status_code=201)
async def create_data(data: DataCreate):
    """새 데이터 추가"""
    db = get_db()
    doc_ref = db.collection("data").document()
    doc_data = {
        "date": data.date,
        "value": data.value,
        "memo": data.memo,
        "created_at": datetime.utcnow().isoformat(),
    }
    doc_ref.set(doc_data)
    return DataResponse(id=doc_ref.id, **data.model_dump())


@router.get("", response_model=list[DataResponse])
async def get_all_data():
    """데이터 목록 조회 (날짜순 정렬)"""
    db = get_db()
    docs = db.collection("data").order_by("date").stream()
    result = []
    for doc in docs:
        d = doc.to_dict()
        result.append(DataResponse(
            id=doc.id,
            date=d.get("date", ""),
            value=d.get("value", 0),
            memo=d.get("memo", ""),
        ))
    return result


@router.put("/{data_id}", response_model=DataResponse)
async def update_data(data_id: str, data: DataUpdate):
    """데이터 수정"""
    db = get_db()
    doc_ref = db.collection("data").document(data_id)
    doc = doc_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="데이터를 찾을 수 없습니다.")

    update_fields = {k: v for k, v in data.model_dump().items() if v is not None}
    if not update_fields:
        raise HTTPException(status_code=400, detail="수정할 필드가 없습니다.")

    doc_ref.update(update_fields)
    updated = doc_ref.get().to_dict()
    return DataResponse(
        id=data_id,
        date=updated.get("date", ""),
        value=updated.get("value", 0),
        memo=updated.get("memo", ""),
    )


@router.delete("/{data_id}")
async def delete_data(data_id: str):
    """데이터 삭제"""
    db = get_db()
    doc_ref = db.collection("data").document(data_id)
    doc = doc_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="데이터를 찾을 수 없습니다.")
    doc_ref.delete()
    return {"message": "삭제 완료", "id": data_id}


@router.get("/summary")
async def get_data_summary():
    """데이터 요약 — AI 시스템 프롬프트 주입용"""
    db = get_db()
    docs = db.collection("data").order_by("date").stream()
    data_list = []
    for doc in docs:
        d = doc.to_dict()
        data_list.append(d)

    if not data_list:
        return {
            "period": "데이터 없음",
            "count": 0,
            "metrics": {},
            "trend": "데이터 부족",
        }

    values = [d["value"] for d in data_list]
    dates = [d["date"] for d in data_list]
    count = len(values)

    # 기본 통계
    avg_val = sum(values) / count
    max_val = max(values)
    min_val = min(values)

    # 최근 추세 계산 (최근 30개 데이터 기준)
    recent = values[-30:] if len(values) >= 30 else values
    if len(recent) >= 2:
        first_half = sum(recent[: len(recent) // 2]) / (len(recent) // 2)
        second_half = sum(recent[len(recent) // 2 :]) / (len(recent) - len(recent) // 2)
        change_pct = ((second_half - first_half) / first_half) * 100
        if change_pct > 3:
            trend = f"상승 ({change_pct:+.1f}%)"
        elif change_pct < -3:
            trend = f"하락 ({change_pct:+.1f}%)"
        else:
            trend = f"보합 ({change_pct:+.1f}%)"
    else:
        trend = "데이터 부족"

    return {
        "period": f"{dates[0]} ~ {dates[-1]}",
        "count": count,
        "metrics": {
            "average": round(avg_val, 2),
            "max": round(max_val, 2),
            "min": round(min_val, 2),
        },
        "trend": trend,
        "data_type": "비트코인 일별 가격 (USD)",
    }
