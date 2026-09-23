"""
다이어트 식단 추천 - 콘텐츠 기반 모델 학습 스크립트

실제 데이터가 아직 없으므로, schema.sql의 meals 테이블 구조와
동일한 형태의 샘플 데이터로 파이프라인을 구성했습니다.
실제 서비스에서는 아래 load_meals() 함수만 실제 DB 조회 코드로
교체하면 나머지 로직은 그대로 재사용 가능합니다.

핵심 아이디어:
1. 각 식단(meal)을 "매크로 영양소 벡터 + 태그 벡터"로 표현
2. 사용자 프로필(목표 칼로리/매크로, 선호 태그)도 같은 공간의 벡터로 변환
3. 알레르기 / 식단타입 부적합 식단은 하드 필터로 제외
4. 남은 식단들과 사용자 벡터 간 코사인 유사도로 랭킹
5. 전처리기(스케일러, 태그 인코더)는 학습된 "모델 아티팩트"로 저장 →
   FastAPI 서버가 이 아티팩트를 로드해서 실시간 추천에 사용
"""

import os
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler, MultiLabelBinarizer
from sklearn.metrics.pairwise import cosine_similarity

from enrich import infer_allergens, infer_diet_types, infer_tags

RAW_DATA_PATH = "meals_raw.json"  # fetch_public_data.py의 출력 파일


# -------------------------------------------------------
# 1. 데이터 로드
#    meals_raw.json이 있으면 실제 공공데이터를 사용,
#    없으면 파이프라인 테스트용 샘플 데이터로 대체
# -------------------------------------------------------
def load_meals() -> pd.DataFrame:
    if os.path.exists(RAW_DATA_PATH):
        return load_real_meals(RAW_DATA_PATH)
    print(f"[안내] {RAW_DATA_PATH}가 없어 샘플 데이터로 실행합니다. "
          f"fetch_public_data.py를 먼저 실행하면 실제 데이터로 전환됩니다.")
    return load_sample_meals()


def load_real_meals(path: str, max_rows: int = None) -> pd.DataFrame:
    """
    fetch_public_data.py가 저장한 meals_raw.json을 읽어서
    태그/식단타입/알레르기를 규칙 기반으로 채운 뒤 DataFrame으로 변환합니다.
    """
    with open(path, "r", encoding="utf-8") as f:
        raw_items = json.load(f)

    if max_rows:
        raw_items = raw_items[:max_rows]

    rows = []
    for idx, item in enumerate(raw_items, start=1):
        # 값이 비정상적인(칼로리 없음/0 이하 등) 항목은 추천 대상에서 제외
        calories = item.get("calories") or 0
        if calories <= 0:
            continue

        macros = {
            "calories": calories,
            "protein": item.get("protein") or 0,
            "carbs": item.get("carbs") or 0,
            "fat": item.get("fat") or 0,
            "sodium": item.get("sodium") or 0,
            "fiber": item.get("fiber") or 0,
        }
        name = item.get("name") or ""
        category = item.get("category") or ""

        rows.append({
            "id": idx,
            "food_cd": item.get("food_cd", ""),
            "name": name,
            "category": category,
            "calories": macros["calories"],
            "protein": macros["protein"],
            "carbs": macros["carbs"],
            "fat": macros["fat"],
            "tags": infer_tags(macros),
            "diet_type_suitable": infer_diet_types(name, category, macros),
            "allergens": infer_allergens(name),
        })

    df = pd.DataFrame(rows)
    print(f"[안내] 실제 데이터 {len(df)}건 로드 완료 (원본 {len(raw_items)}건 중 "
          f"칼로리 0 이하 등 이상치 제외)")
    return df


def load_sample_meals() -> pd.DataFrame:
    sample_meals = [
        {"id": 1, "name": "닭가슴살 샐러드", "category": "샐러드",
         "calories": 320, "protein": 35, "carbs": 15, "fat": 10,
         "tags": ["고단백", "저탄수화물"], "diet_type_suitable": ["일반", "저탄수"],
         "allergens": []},
        {"id": 2, "name": "연어 스테이크", "category": "양식",
         "calories": 450, "protein": 40, "carbs": 10, "fat": 25,
         "tags": ["고단백", "오메가3"], "diet_type_suitable": ["일반", "키토"],
         "allergens": ["생선"]},
        {"id": 3, "name": "두부 야채볶음", "category": "한식",
         "calories": 280, "protein": 18, "carbs": 25, "fat": 12,
         "tags": ["비건", "저칼로리"], "diet_type_suitable": ["일반", "비건"],
         "allergens": []},
        {"id": 4, "name": "새우 볶음밥", "category": "한식",
         "calories": 520, "protein": 22, "carbs": 70, "fat": 14,
         "tags": ["매운맛"], "diet_type_suitable": ["일반"],
         "allergens": ["갑각류"]},
        {"id": 5, "name": "그릭요거트 볼", "category": "샐러드",
         "calories": 250, "protein": 20, "carbs": 30, "fat": 6,
         "tags": ["고단백", "저칼로리"], "diet_type_suitable": ["일반", "저탄수"],
         "allergens": ["유제품"]},
        {"id": 6, "name": "렌틸콩 스튜", "category": "양식",
         "calories": 300, "protein": 19, "carbs": 40, "fat": 5,
         "tags": ["비건", "고식이섬유"], "diet_type_suitable": ["일반", "비건"],
         "allergens": []},
        {"id": 7, "name": "훈제오리 샐러드", "category": "샐러드",
         "calories": 400, "protein": 28, "carbs": 12, "fat": 26,
         "tags": ["고지방", "저탄수화물"], "diet_type_suitable": ["일반", "키토"],
         "allergens": []},
        {"id": 8, "name": "현미 비빔밥", "category": "한식",
         "calories": 480, "protein": 15, "carbs": 75, "fat": 10,
         "tags": ["비건", "고식이섬유"], "diet_type_suitable": ["일반", "비건"],
         "allergens": []},
    ]
    return pd.DataFrame(sample_meals)


# -------------------------------------------------------
# 2. 전처리기 학습 (매크로 스케일러 + 태그 인코더)
# -------------------------------------------------------
def fit_preprocessors(meals: pd.DataFrame):
    macro_cols = ["calories", "protein", "carbs", "fat"]
    scaler = StandardScaler()
    scaler.fit(meals[macro_cols])

    mlb_tags = MultiLabelBinarizer()
    mlb_tags.fit(meals["tags"])

    return scaler, mlb_tags


def build_feature_matrix(meals: pd.DataFrame, scaler: StandardScaler,
                          mlb_tags: MultiLabelBinarizer) -> np.ndarray:
    macro_cols = ["calories", "protein", "carbs", "fat"]
    macro_scaled = scaler.transform(meals[macro_cols])
    tag_encoded = mlb_tags.transform(meals["tags"])
    # 매크로와 태그 가중치를 다르게 주고 싶으면 여기서 곱해서 조정 가능
    return np.hstack([macro_scaled, tag_encoded])


# -------------------------------------------------------
# 3. 사용자 프로필 -> 같은 벡터 공간으로 변환
# -------------------------------------------------------
def build_user_vector(user_profile: dict, scaler: StandardScaler,
                       mlb_tags: MultiLabelBinarizer, meals_per_day: int = 3) -> np.ndarray:
    """
    사용자의 일일 목표를 한 끼 기준으로 환산해서 meal 벡터와 같은 공간에 놓습니다.
    """
    target_cal = user_profile["daily_calorie_target"] / meals_per_day
    target_protein = (user_profile.get("daily_protein_target")
                       or target_cal * 0.3 / 4)  # 단백질 목표 없으면 칼로리의 30%를 단백질로 가정
    # carbs/fat은 대략적인 기본 비율로 역산 (실제 서비스에서는 더 정교하게 설계 가능)
    target_carbs = target_cal * 0.4 / 4
    target_fat = target_cal * 0.3 / 9

    macro_vec = scaler.transform([[target_cal, target_protein, target_carbs, target_fat]])
    tag_vec = mlb_tags.transform([user_profile.get("preferred_tags", [])])
    return np.hstack([macro_vec, tag_vec])


# -------------------------------------------------------
# 4. 하드 필터: 알레르기 / 식단타입 부적합 제외
# -------------------------------------------------------
def hard_filter(meals: pd.DataFrame, user_profile: dict) -> pd.DataFrame:
    allergies = set(user_profile.get("allergies", []))
    diet_type = user_profile.get("diet_type", "일반")

    def is_safe(row):
        if allergies.intersection(set(row["allergens"])):
            return False
        if diet_type not in row["diet_type_suitable"]:
            return False
        return True

    return meals[meals.apply(is_safe, axis=1)].reset_index(drop=True)


# -------------------------------------------------------
# 5. 추천 실행
# -------------------------------------------------------
def recommend(user_profile: dict, meals: pd.DataFrame, scaler, mlb_tags, top_k: int = 3):
    safe_meals = hard_filter(meals, user_profile)
    if safe_meals.empty:
        return []

    meal_matrix = build_feature_matrix(safe_meals, scaler, mlb_tags)
    user_vec = build_user_vector(user_profile, scaler, mlb_tags)

    sims = cosine_similarity(user_vec, meal_matrix)[0]
    safe_meals = safe_meals.copy()
    safe_meals["score"] = sims
    ranked = safe_meals.sort_values("score", ascending=False).head(top_k)

    return ranked[["id", "name", "calories", "protein", "carbs", "fat", "tags", "score"]].to_dict(orient="records")


# -------------------------------------------------------
# 6. 학습 실행 + 아티팩트 저장
# -------------------------------------------------------
if __name__ == "__main__":
    meals = load_meals()
    scaler, mlb_tags = fit_preprocessors(meals)

    # 아티팩트 저장: FastAPI 서버가 이 파일들을 로드해서 서빙에 사용
    joblib.dump(scaler, "scaler.joblib")
    joblib.dump(mlb_tags, "tag_encoder.joblib")
    meals.to_json("meals.json", orient="records", force_ascii=False)

    print("전처리기 학습 완료 -> scaler.joblib, tag_encoder.joblib, meals.json 저장됨")

    # 간단한 테스트 추천
    test_user = {
        "goal": "감량",
        "daily_calorie_target": 1500,
        "diet_type": "일반",
        "allergies": ["갑각류"],
        "preferred_tags": ["고단백", "저탄수화물"],
    }
    results = recommend(test_user, meals, scaler, mlb_tags, top_k=3)
    print("\n[테스트 추천 결과]")
    for r in results:
        print(f"- {r['name']} (유사도: {r['score']:.3f}, {r['calories']}kcal, 태그: {r['tags']})")
