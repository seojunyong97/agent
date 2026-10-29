"""
BTC Insight — 비트코인 데이터 분석 AI 비서
FastAPI 백엔드 메인 엔트리포인트
"""

import os
import random
import httpx
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
    """CoinGecko에서 실제 비트코인 가격을 가져와 Firestore에 업로드"""
    db = get_db()

    # 기존 데이터 삭제
    existing = db.collection("data").stream()
    for doc in existing:
        doc.reference.delete()

    # CoinGecko API로 실제 비트코인 가격 가져오기 (최대 365일씩)
    all_prices = []

    # 2024-01-01 ~ 오늘까지 구간을 나눠서 요청
    start_ts = int(datetime(2024, 1, 1).timestamp())
    now_ts = int(datetime.utcnow().timestamp())

    # 365일 단위로 나눠서 요청 (CoinGecko 무료 제한)
    current_start = start_ts
    async with httpx.AsyncClient() as client:
        while current_start < now_ts:
            current_end = min(current_start + 365 * 86400, now_ts)
            url = (
                f"https://api.coingecko.com/api/v3/coins/bitcoin/market_chart/range"
                f"?vs_currency=usd&from={current_start}&to={current_end}"
            )
            resp = await client.get(url, timeout=30)
            if resp.status_code == 200:
                prices = resp.json().get("prices", [])
                all_prices.extend(prices)
            current_start = current_end

    if not all_prices:
        return {"message": "CoinGecko에서 데이터를 가져오지 못했습니다.", "count": 0}

    # 날짜별 평균 가격으로 정리 (중복 날짜 제거)
    daily = {}
    for ts, price in all_prices:
        date_str = datetime.utcfromtimestamp(ts / 1000).strftime("%Y-%m-%d")
        if date_str not in daily:
            daily[date_str] = []
        daily[date_str].append(price)

    data_list = []
    sorted_dates = sorted(daily.keys())
    prev_price = None

    for date_str in sorted_dates:
        avg_price = sum(daily[date_str]) / len(daily[date_str])

        # 전일 대비 변동률로 메모 생성
        if prev_price:
            change = (avg_price - prev_price) / prev_price
            if change > 0.05:
                memo = "급등"
            elif change > 0.02:
                memo = "상승"
            elif change < -0.05:
                memo = "급락"
            elif change < -0.02:
                memo = "하락"
            else:
                memo = "보합"
        else:
            memo = "보합"

        prev_price = avg_price
        data_list.append({
            "date": date_str,
            "value": round(avg_price, 2),
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
    return {
        "message": "실제 비트코인 가격 데이터 업로드 완료!",
        "count": len(data_list),
        "period": f"{sorted_dates[0]} ~ {sorted_dates[-1]}",
    }
