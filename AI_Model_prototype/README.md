# 다이어트 식단 추천 - Python 서버

## 파일 구성
- `schema.sql` : 자바 DB 스키마 (users, user_profile, meals, user_meal_logs)
- `train_model.py` : 콘텐츠 기반 추천 로직 + 전처리기 학습 (샘플 데이터 포함)
- `serve.py` : FastAPI 서빙 서버 (자바가 호출할 엔드포인트)

## 파일 구성 (추가)
- `.env.example` : 공공데이터포털 API 키 저장용 (→ `.env`로 복사해서 사용)
- `fetch_public_data.py` : 식약처 식품영양성분DB API에서 데이터 수집 → `meals_raw.json` 생성
- `enrich.py` : 공공데이터에 없는 태그/식단타입/알레르기를 규칙 기반으로 자동 추론

## 실행 순서

```bash
pip install scikit-learn pandas joblib fastapi uvicorn requests python-dotenv

# 0) API 키 설정
cp .env.example .env
# .env 파일 열어서 DATA_GO_KR_API_KEY에 발급받은 인증키 붙여넣기

# 1) 공공데이터 수집 -> meals_raw.json 생성
#    (전체 30만 건, 시간 걸리므로 처음엔 fetch_public_data.py의
#     "if page > 5: break" 주석 해제해서 일부만 테스트 추천)
python fetch_public_data.py

# 2) 모델(전처리기) 학습 -> scaler.joblib, tag_encoder.joblib, meals.json 생성
#    meals_raw.json이 있으면 자동으로 실제 데이터를 사용합니다.
python train_model.py

# 3) 서버 실행
uvicorn serve:app --host 0.0.0.0 --port 8000
```

## 자바에서 호출하는 방법

```
POST http://localhost:8000/recommend
Content-Type: application/json

{
  "goal": "감량",
  "daily_calorie_target": 1500,
  "diet_type": "일반",
  "allergies": ["갑각류"],
  "preferred_tags": ["고단백", "저탄수화물"],
  "top_k": 3
}
```

Spring Boot에서는 `WebClient`나 `RestTemplate`으로 위 요청을 그대로 보내면 됩니다.

## 지금 당장 해야 할 일 (우선순위 순)

1. **`train_model.py`의 `load_meals()` 함수를 실제 DB 쿼리로 교체**
   - `schema.sql`의 `meals` 테이블 구조와 컬럼명을 동일하게 맞춰뒀으므로,
     실제 식단 데이터가 준비되면 이 함수만 바꾸면 나머지 파이프라인은 그대로 동작합니다.
2. **자바 쪽에서 `user_meal_logs` 테이블에 로그 쌓기 시작**
   - 서비스 초기부터 이 데이터를 모아야, 나중에 "이 사용자와 비슷한 사람들이
     선택한 식단"을 반영하는 협업 필터링으로 업그레이드할 수 있습니다.
3. **실제 식단 데이터가 30~50개 이상 쌓이면 추천 품질을 다시 확인**
   - 지금은 샘플 8개라 유사도 랭킹이 단순합니다. 데이터가 늘어나면
     태그 체계(예: "저탄수화물", "고단백" 외에 더 세분화된 태그)를 추가로 설계하는 게 좋습니다.

## 다음 단계 (데이터 쌓인 후)

- `user_meal_logs`가 충분히 쌓이면 (수백~수천 건 이상), 협업 필터링 모델
  (예: `surprise` 라이브러리의 SVD, 또는 implicit feedback용 ALS)을 추가해서
  콘텐츠 기반 점수와 가중 평균하는 하이브리드 방식으로 업그레이드 가능합니다.
