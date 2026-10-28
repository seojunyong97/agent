# ₿ BTC Insight — 비트코인 데이터 분석 AI 비서

## 📌 서비스 소개

BTC Insight는 비트코인 일별 가격 데이터를 분석하고, AI가 해당 데이터를 기반으로 맞춤형 답변을 제공하는 웹 서비스입니다.

일반적인 ChatGPT는 내 데이터를 모르지만, BTC Insight의 AI 비서는 저장된 비트코인 가격 데이터의 요약 정보를 시스템 프롬프트에 주입(컨텍스트 주입)하여, "최근 추세가 어때?", "최고가는 얼마였어?" 같은 질문에 **데이터 기반 맞춤형 답변**을 제공합니다.

---

## 🛠 기술 스택

| 구분 | 기술 |
|------|------|
| **백엔드** | Python 3.10+, FastAPI, Uvicorn |
| **데이터베이스** | Firebase Firestore |
| **AI** | Google Gemini 3.8 Flash |
| **프론트엔드** | HTML / CSS / JavaScript (바닐라) |
| **백엔드 배포** | Render |
| **프론트엔드 배포** | Vercel |

---

## 🔗 배포 URL

| 서비스 | URL |
|--------|-----|
| **프론트엔드** | https://agent-frontend-ruby-delta.vercel.app |
| **백엔드 API** | https://agent-8lk2.onrender.com |
| **Swagger UI** | https://agent-8lk2.onrender.com/docs |

> ⚠️ Render 무료 티어 사용 시 첫 요청에 30초 정도 지연(콜드스타트)이 발생할 수 있습니다.

---

## 🚀 로컬 실행 방법

### 백엔드

```bash
cd backend

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 패키지 설치
pip install -r requirements.txt

# 환경변수 설정
cp .env.example .env
# .env 파일에 실제 키 입력

# 서버 실행
uvicorn main:app --reload --port 8000
```

### 프론트엔드

```bash
cd frontend

# Live Server 등으로 index.html 열기
# 또는 Python 간이 서버
python -m http.server 5500
```

### 시드 데이터 업로드

```bash
cd backend
python seed_data.py
# Firestore에 180개 비트코인 가격 데이터 업로드
```

---

## 🔐 환경 변수 목록

### 백엔드 (.env)

| 변수명 | 설명 |
|--------|------|
| `GEMINI_API_KEY` | Google Gemini API 키 |
| `FIREBASE_SERVICE_ACCOUNT_JSON` | Firebase 서비스 계정 키 (JSON 문자열) |
| `ALLOWED_ORIGINS` | CORS 허용 도메인 (쉼표 구분) |

### 프론트엔드 (Vercel 환경변수 또는 app.js 수정)

| 변수명 | 설명 |
|--------|------|
| `API_BASE` | 백엔드 API 서버 URL (app.js에 직접 설정) |

---

## 📸 주요 화면

### 1. 데이터 요약이 보이는 채팅 화면
- 좌측 사이드바에 데이터 요약 (기간, 평균, 최고/최저, 트렌드)
- AI에게 질문하면 데이터 기반 맞춤 답변

### 2. 데이터 관리 화면
- 데이터 추가 / 목록 조회 / 수정 / 삭제 (CRUD)

### 3. 대화 기록 화면
- 이전 대화 목록 조회
- 대화 불러오기 / 삭제

---

## 📁 프로젝트 구조

```
ai-agent-project/
├── backend/
│   ├── main.py              # FastAPI 앱 진입점
│   ├── requirements.txt     # Python 패키지
│   ├── render.yaml          # Render 배포 설정
│   ├── seed_data.py         # 시드 데이터 생성/업로드
│   ├── .env.example         # 환경변수 템플릿
│   ├── models/
│   │   └── schemas.py       # Pydantic 모델
│   ├── routers/
│   │   ├── data.py          # 데이터 CRUD + 요약 API
│   │   ├── conversations.py # 대화 기록 API
│   │   └── chat.py          # AI 챗봇 API (컨텍스트 주입)
│   └── services/
│       ├── firebase.py      # Firestore 초기화
│       └── openai_service.py # Gemini API 호출
├── frontend/
│   ├── index.html           # 메인 HTML
│   ├── style.css            # 스타일시트
│   ├── app.js               # 프론트엔드 로직
│   └── vercel.json          # Vercel 설정
└── README.md
```

---

## 📊 API 엔드포인트

### 데이터 관리
- `POST /api/data` — 새 데이터 추가
- `GET /api/data` — 데이터 목록 조회
- `PUT /api/data/{id}` — 데이터 수정
- `DELETE /api/data/{id}` — 데이터 삭제
- `GET /api/data/summary` — 데이터 요약 (AI 프롬프트 주입용)

### AI 채팅
- `POST /api/chat` — AI 대화 (컨텍스트 주입 방식)

### 대화 기록
- `POST /api/conversations` — 대화 저장
- `GET /api/conversations` — 대화 목록
- `GET /api/conversations/{id}` — 특정 대화 불러오기
- `DELETE /api/conversations/{id}` — 대화 삭제

---

## ⚡ 핵심 아키텍처: 컨텍스트 주입

```
사용자 질문 → /api/chat
  ↓
데이터 요약 조회 (/api/data/summary)
  ↓
시스템 프롬프트에 요약 삽입
  ↓
Gemini API 호출
  ↓
AI 응답 반환 + Firestore에 대화 자동 저장
```
