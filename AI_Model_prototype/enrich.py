"""
공공데이터(식품영양성분DB)에는 태그/식단타입/알레르기 정보가 없기 때문에,
매크로 영양소 수치와 식품명/카테고리 키워드를 기반으로 규칙 기반 추론을 합니다.

이 규칙들은 "완벽한 정답"이 아니라 "합리적인 기본값"입니다.
실제 서비스에서는 영양사 검수를 거치거나, 사용자 피드백으로 보정하는 걸 권장합니다.
"""

import re

# 알레르기 키워드 -> 식품명에 해당 키워드가 포함되면 그 알레르기 유발 요소로 태깅
ALLERGEN_KEYWORDS = {
    "갑각류": ["새우", "게", "가재", "랍스터"],
    "생선": ["고등어", "연어", "갈치", "삼치", "참치", "명태", "동태", "조기"],
    "유제품": ["우유", "치즈", "버터", "요거트", "생크림", "크림"],
    "계란": ["계란", "달걀"],
    "밀": ["밀가루", "빵", "면", "국수", "파스타", "라면"],
    "땅콩": ["땅콩"],
    "대두": ["두부", "콩", "된장", "간장"],
}


def infer_allergens(food_name: str) -> list:
    food_name = food_name or ""
    found = []
    for allergen, keywords in ALLERGEN_KEYWORDS.items():
        if any(kw in food_name for kw in keywords):
            found.append(allergen)
    return found


# 카테고리/식품명 키워드로 채식 여부를 보수적으로 추정
NON_VEGAN_KEYWORDS = [
    "고기", "돼지", "소고기", "닭", "오리", "육류", "생선", "어류", "새우", "게",
    "계란", "달걀", "우유", "치즈", "버터", "젓갈", "육수",
]


def infer_diet_types(food_name: str, category: str, macros: dict) -> list:
    food_name = food_name or ""
    category = category or ""
    diet_types = ["일반"]

    is_non_vegan = any(kw in food_name or kw in category for kw in NON_VEGAN_KEYWORDS)
    if not is_non_vegan:
        diet_types.append("비건")

    if macros["carbs"] < 15:
        diet_types.append("저탄수")

    if macros["fat"] >= 15 and macros["carbs"] < 15:
        diet_types.append("키토")

    if macros.get("sodium", 0) and macros["sodium"] < 300:
        diet_types.append("저염")

    return diet_types


def infer_tags(macros: dict) -> list:
    tags = []
    calories = macros["calories"]
    protein = macros["protein"]
    carbs = macros["carbs"]
    fat = macros["fat"]
    sodium = macros.get("sodium", 0)
    fiber = macros.get("fiber", 0)

    # 100kcal당 단백질 비율로 "고단백" 판단 (단순 절대값보다 공정한 기준)
    if calories > 0 and (protein / calories) * 100 >= 15:
        tags.append("고단백")
    if carbs < 10:
        tags.append("저탄수화물")
    if calories < 200:
        tags.append("저칼로리")
    if fat >= 15:
        tags.append("고지방")
    if sodium and sodium < 300:
        tags.append("저염")
    if fiber and fiber >= 3:
        tags.append("고식이섬유")

    return tags
