"""
비트코인 일별 가격 시드 데이터 생성 스크립트
Firestore에 100개 이상의 데이터 포인트를 업로드한다.
실행: python seed_data.py
"""

import os
import json
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore

load_dotenv()


def generate_btc_data(num_days=180):
    """
    리얼리스틱한 비트코인 가격 데이터 생성 (180일분)
    2026-05-03 ~ 2026-10-29 기간의 시뮬레이션 데이터
    실제 2026년 10월 기준 ~$83,000 수준에 맞춤
    """
    data = []
    # 오늘(2026-10-29)부터 180일 전 = 2026-05-03
    end_date = datetime(2026, 10, 29)
    start_date = end_date - timedelta(days=num_days - 1)
    price = 72000  # 시작 가격 (2026년 5월 초 추정)

    for i in range(num_days):
        current_date = start_date + timedelta(days=i)

        # 랜덤 변동 + 약간의 상승 추세 (최종 ~$83,000 도달)
        daily_change = random.gauss(0.0008, 0.025)  # 완만한 상승
        price *= (1 + daily_change)
        price = max(price, 50000)  # 최소 $50,000

        # 마지막 날은 실제 가격에 맞춤
        if i == num_days - 1:
            price = 83039

        # 메모 생성
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

        data.append({
            "date": current_date.strftime("%Y-%m-%d"),
            "value": round(price, 2),
            "memo": memo,
            "created_at": datetime.utcnow().isoformat(),
        })

    return data


def upload_to_firestore(data_list):
    """Firestore에 데이터 업로드"""
    service_account_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
    if not service_account_json:
        print("❌ FIREBASE_SERVICE_ACCOUNT_JSON 환경변수가 없습니다.")
        print("   .env 파일에 설정해주세요.")
        return

    service_account_info = json.loads(service_account_json)
    cred = credentials.Certificate(service_account_info)

    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)

    db = firestore.client()

    # 기존 data 컬렉션 비우기
    print("🗑️  기존 데이터 삭제 중...")
    existing = db.collection("data").stream()
    for doc in existing:
        doc.reference.delete()

    # 새 데이터 업로드
    print(f"📤 {len(data_list)}개 데이터 업로드 중...")
    batch = db.batch()
    for i, item in enumerate(data_list):
        doc_ref = db.collection("data").document()
        batch.set(doc_ref, item)

        # Firestore 배치 제한 (500개)
        if (i + 1) % 400 == 0:
            batch.commit()
            batch = db.batch()
            print(f"   {i + 1}개 완료...")

    batch.commit()
    print(f"✅ 총 {len(data_list)}개 데이터 업로드 완료!")


def save_to_json(data_list, filename="seed_data.json"):
    """JSON 파일로도 저장 (백업용)"""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data_list, f, ensure_ascii=False, indent=2)
    print(f"💾 {filename}에 저장 완료")


if __name__ == "__main__":
    print("🪙 비트코인 시드 데이터 생성 시작")
    print("=" * 40)

    data = generate_btc_data(180)

    print(f"📊 생성된 데이터: {len(data)}개")
    print(f"   기간: {data[0]['date']} ~ {data[-1]['date']}")

    values = [d["value"] for d in data]
    print(f"   평균: ${sum(values)/len(values):,.2f}")
    print(f"   최고: ${max(values):,.2f}")
    print(f"   최저: ${min(values):,.2f}")

    # JSON 파일로 저장
    save_to_json(data)

    # Firestore 업로드
    upload = input("\nFirestore에 업로드하시겠습니까? (y/n): ").strip().lower()
    if upload == "y":
        upload_to_firestore(data)
    else:
        print("업로드 건너뜀. seed_data.json을 참고하세요.")
