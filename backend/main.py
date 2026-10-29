"""
BTC Insight — 비트코인 데이터 분석 AI 비서
FastAPI 백엔드 메인 엔트리포인트
"""

import os
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import data, conversations, chat
from services.firebase import get_db

# 환경변수 로드
load_dotenv()

# FastAPI 앱 초기화
app = FastAPI(
    title="BTC Insight API",
    description="비트코인 데이터 기반 AI 비서 백엔드",
    version="1.0.0",
)

# CORS 설정
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5500").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(data.router)
app.include_router(conversations.router)
app.include_router(chat.router)


@app.get("/", tags=["상태"])
async def root():
    return {
        "service": "BTC Insight API",
        "status": "running",
        "docs": "/docs",
        "message": "비트코인 데이터 분석 AI 비서 API입니다.",
    }


@app.get("/health", tags=["상태"])
async def health_check():
    return {"status": "healthy"}


@app.post("/api/seed", tags=["관리"])
async def seed_data():
    """비트코인 시드 데이터 180개 생성 및 업로드 — 기존 데이터 삭제 후 교체"""
    db = get_db()

    # 기존 데이터 삭제
    existing = db.collection("data").stream()
    for doc in existing:
        doc.reference.delete()

    # 2024-01-01 ~ 2026-10-29 데이터 생성
    data_list = []
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2026, 10, 29)
    num_days = (end_date - start_date).days + 1
    price = 42000.0  # 2024년 1월 초 비트코인 가격

    for i in range(num_days):
        current_date = start_date + timedelta(days=i)
        daily_change = random.gauss(0.0008, 0.025)
        price *= (1 + daily_change)
        price = max(price, 50000)

        # 마지막 날은 실제 가격에 맞춤
        if i == num_days - 1:
            price = 83039.0

        if daily_change > 0.05:
            memo = "급등"
        elif daily_change > 0.02:
            memo = "상승"
        elif daily_change < -0.05:
            memo = "급락"
        elif daily_change < -0.02:
            memo = "하락"
        else:
            memo = "보합"

        data_list.append({
            "date": current_date.strftime("%Y-%m-%d"),
            "value": round(price, 2),
            "memo": memo,
            "created_at": datetime.utcnow().isoformat(),
        })

    # Firestore 업로드
    batch = db.batch()
    for i, item in enumerate(data_list):
        doc_ref = db.collection("data").document()
        batch.set(doc_ref, item)
        if (i + 1) % 400 == 0:
            batch.commit()
            batch = db.batch()

    batch.commit()
    return {"message": "시드 데이터 업로드 완료!", "count": len(data_list)}
