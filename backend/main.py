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
    """비트코인 시드 데이터 180개 생성 및 업로드 (1회용)"""
    db = get_db()
    # 이미 데이터가 있으면 스킵
    existing = db.collection("data").limit(1).get()
    if len(existing) > 0:
        return {"message": "이미 데이터가 존재합니다.", "count": 0}

    data_list = []
    start_date = datetime(2024, 7, 1)
    price = 62000.0
    random.seed(42)

    for i in range(180):
        current_date = start_date + timedelta(days=i)
        daily_change = random.gauss(0.002, 0.03)
        price *= (1 + daily_change)
        price = max(price, 20000)

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
