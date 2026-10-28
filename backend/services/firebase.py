"""Firebase Firestore 초기화 및 DB 인스턴스 제공"""

import os
import json
import firebase_admin
from firebase_admin import credentials, firestore

_db = None


def get_db():
    """Firestore 클라이언트 싱글턴 반환"""
    global _db
    if _db is not None:
        return _db

    # 환경변수에서 서비스 계정 JSON 읽기
    service_account_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
    if not service_account_json:
        raise RuntimeError("FIREBASE_SERVICE_ACCOUNT_JSON 환경변수가 설정되지 않았습니다.")

    service_account_info = json.loads(service_account_json)
    cred = credentials.Certificate(service_account_info)

    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)

    _db = firestore.client()
    return _db
