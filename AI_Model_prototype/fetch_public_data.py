"""
공공데이터포털 - 식품의약품안전처_식품영양성분DB정보 API 호출 스크립트

사용법:
1. .env.example을 .env로 복사하고 발급받은 인증키를 넣으세요.
2. pip install requests python-dotenv
3. 아래 [[ 채워야 할 부분 ]] 표시된 곳을 data.go.kr 활용신청 상세페이지의
   "참고문서" / Swagger 명세에 나온 실제 값으로 채우세요.
   (로그인 후 마이페이지 > 개발계정 상세보기 > 활용신청 목록에서 확인 가능)
4. python fetch_public_data.py

이 스크립트가 하는 일:
- API를 페이지 단위로 호출해서 전체 데이터를 수집
- meals 테이블(schema.sql) 컬럼 형식으로 변환
- meals_raw.json으로 저장 -> train_model.py의 load_meals()에서 이 파일을 읽도록 교체하면 됨
"""

import os
import time
import json
import requests
from dotenv import load_dotenv

load_dotenv()  # .env 파일에서 DATA_GO_KR_API_KEY 읽어옴

# 인증키가 이미 URL 인코딩되어 있으므로, requests의 params에 넣으면 이중 인코딩됩니다.
# 그래서 URL 문자열에 직접 붙여서 사용합니다.
API_KEY_ENCODED = os.environ["DATA_GO_KR_API_KEY"]  # .env에 인코딩된 키 그대로 저장

BASE_URL = "https://apis.data.go.kr/1471000/FoodNtrCpntDbInfo02/getFoodNtrCpntDbInq02"

NUM_OF_ROWS = 100        # 한 번에 가져올 개수
OUTPUT_PATH = "meals_raw.json"
CHECKPOINT_EVERY = 20    # 20페이지(=2000건)마다 중간 저장
MAX_RETRIES = 5          # 페이지 하나당 최대 재시도 횟수
RETRY_BACKOFF_SEC = 3    # 재시도 사이 대기 시간(점점 늘어남)


def fetch_page(page_no: int) -> dict:
    url = f"{BASE_URL}?serviceKey={API_KEY_ENCODED}&pageNo={page_no}&numOfRows={NUM_OF_ROWS}&type=json"

    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            last_error = e
            wait = RETRY_BACKOFF_SEC * attempt
            print(f"  [{page_no}페이지] 요청 실패 ({attempt}/{MAX_RETRIES}), {wait}초 후 재시도: {e}")
            time.sleep(wait)
    raise last_error


def extract_items(page_json: dict) -> list:
    # 확인된 실제 응답 구조: header.resultCode / body.items
    if page_json.get("header", {}).get("resultCode") != "00":
        print("API 오류:", page_json.get("header"))
        return []
    return page_json.get("body", {}).get("items", [])


def _to_float(value) -> float:
    try:
        return float(value) if value not in (None, "") else 0.0
    except ValueError:
        return 0.0


# AMT_NUM 순서는 한국 표준 식품성분표 고정 순서를 따르는 것으로 추정됩니다.
# (에너지, 수분, 단백질, 지방, 회분, 탄수화물, 당류, 식이섬유, 칼슘, 철... 순)
# data.go.kr 상세페이지의 "AMT_NUM 항목코드 정의서" 참고자료로 꼭 한 번 대조 확인하세요.
def map_to_meal(item: dict) -> dict:
    return {
        "food_cd": item.get("FOOD_CD", ""),
        "name": item.get("FOOD_NM_KR", ""),                 # 식품명
        "category": item.get("FOOD_CAT1_NM", ""),           # 대분류 (예: 밥류)
        "sub_category": item.get("FOOD_CAT2_NM", ""),       # 소분류
        "serving_size": item.get("SERVING_SIZE", ""),       # 기준량 (예: "100g")
        "calories": _to_float(item.get("AMT_NUM1")),        # 에너지 (kcal)
        "moisture": _to_float(item.get("AMT_NUM2")),        # 수분 (g)
        "protein": _to_float(item.get("AMT_NUM3")),         # 단백질 (g)
        "fat": _to_float(item.get("AMT_NUM4")),              # 지방 (g)
        "ash": _to_float(item.get("AMT_NUM5")),              # 회분 (g)
        "carbs": _to_float(item.get("AMT_NUM6")),            # 탄수화물 (g)
        "sugar": _to_float(item.get("AMT_NUM7")),            # 당류 (g)
        "fiber": _to_float(item.get("AMT_NUM8")),            # 식이섬유 (g)
        "sodium": _to_float(item.get("AMT_NUM13")),          # 나트륨 (mg)
        "tags": [],                 # 이 API엔 태그가 없음 -> 매크로 기준으로 후처리 규칙 부여 필요
        "diet_type_suitable": ["일반"],  # 기본값, 필요시 매크로 기준으로 후처리 부여
        "allergens": [],             # 이 API엔 알레르기 정보 없음 -> 식품명/원재료 기반 후처리 필요
    }


def load_existing() -> tuple[list, int]:
    """
    이전에 저장된 meals_raw.json이 있으면 이어받기 위해 로드합니다.
    반환: (지금까지 수집된 데이터, 다음에 요청할 페이지 번호)
    """
    if not os.path.exists(OUTPUT_PATH):
        return [], 1

    with open(OUTPUT_PATH, "r", encoding="utf-8") as f:
        existing = json.load(f)

    # 몇 건을 받았었는지로 다음 페이지를 역산 (NUM_OF_ROWS 단위)
    next_page = (len(existing) // NUM_OF_ROWS) + 1
    print(f"[이어받기] 기존에 저장된 {len(existing)}건 발견 -> {next_page}페이지부터 이어서 받습니다.")
    return existing, next_page


def save_checkpoint(meals: list):
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(meals, f, ensure_ascii=False, indent=2)


def fetch_all() -> list:
    all_meals, page = load_existing()

    while True:
        try:
            page_json = fetch_page(page)
        except requests.exceptions.RequestException as e:
            print(f"\n[중단] {page}페이지에서 재시도 한도 초과: {e}")
            print(f"지금까지 받은 {len(all_meals)}건은 이미 저장되어 있습니다.")
            print("네트워크가 안정되면 스크립트를 다시 실행하세요 — 자동으로 이어받습니다.")
            save_checkpoint(all_meals)
            return all_meals

        items = extract_items(page_json)
        if not items:
            print("더 이상 받을 데이터가 없습니다. 수집 완료.")
            break

        all_meals.extend(map_to_meal(item) for item in items)
        print(f"{page}페이지 수집 완료 (누적 {len(all_meals)}건)")

        if page % CHECKPOINT_EVERY == 0:
            save_checkpoint(all_meals)
            print(f"  -> 중간 저장 완료 ({len(all_meals)}건)")

        page += 1
        time.sleep(0.2)  # 과도한 요청 방지

        # 테스트 단계에서는 아래 줄 주석 해제해서 5페이지만 받아보는 걸 추천
        # if page > 5: break

    return all_meals


if __name__ == "__main__":
    meals = fetch_all()
    save_checkpoint(meals)
    print(f"\n총 {len(meals)}건 저장 완료 -> {OUTPUT_PATH}")
    print("이제 train_model.py를 실행하면 이 데이터를 자동으로 사용합니다.")