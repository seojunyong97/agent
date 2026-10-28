"""
BTC Insight — 비트코인 데이터 분석 AI 비서
FastAPI 백엔드 메인 엔트리포인트
"""

import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import data, conversations, chat

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
