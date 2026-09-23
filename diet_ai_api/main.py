from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import random

app = FastAPI(
    title="Diet Menu Recommendation API",
    description="API for recommending diet menus based on available ingredients and condiments.",
    version="1.0.0"
)

# 자바(클라이언트)에서 보내올 요청 데이터 구조 정의
class DietRequest(BaseModel):
    ingredients: List[str]          # 사용자가 입력한 식재료 목록
    condiments: List[str]           # 가입 시 입력받은 조미료 목록
    target_calories: Optional[int] = 500  # 목표 칼로리 (선택사항)
    allergies: Optional[List[str]] = []   # 알레르기 정보 (선택사항)

# 모델이 반환할 추천 메뉴 데이터 구조
class MenuRecommendation(BaseModel):
    menu_name: str                  # 추천 메뉴 이름
    used_ingredients: List[str]     # 사용된 식재료
    used_condiments: List[str]      # 사용된 조미료
    estimated_calories: int         # 예상 칼로리
    recipe_description: str         # 간단한 조리법

# 최종 응답 데이터 구조
class DietResponse(BaseModel):
    recommendations: List[MenuRecommendation]

# AI 모델 클래스 (실제 학습된 모델을 불러와서 사용하는 부분)
class DietRecommendationModel:
    def __init__(self):
        # TODO: 학습된 음식 성분표 기반 모델 로드 (예: joblib.load('model.pkl'), PyTorch, TensorFlow 모델 로드)
        # self.model = load_model(...)
        pass
    
    def predict(self, ingredients: List[str], condiments: List[str], target_calories: int) -> List[MenuRecommendation]:
        # TODO: 실제 AI 모델의 추론(Inference) 로직 구현
        # 현재는 프로토타입 형태의 더미 로직으로 동작합니다.
        
        if not ingredients:
            return []
            
        # 임의로 재료를 선택하여 메뉴 추천 결과를 만듭니다 (테스트용)
        sampled_ingredients = random.sample(ingredients, min(3, len(ingredients)))
        menu_name = f"{' & '.join(sampled_ingredients)} 다이어트 특선"
        
        rec = MenuRecommendation(
            menu_name=menu_name,
            used_ingredients=sampled_ingredients,
            used_condiments=condiments[:2] if condiments else [], 
            estimated_calories=target_calories - random.randint(10, 50),
            recipe_description=f"준비된 {', '.join(sampled_ingredients)}에 적절한 조미료를 곁들여 맛있고 건강하게 조리합니다."
        )
        return [rec]

# 모델 인스턴스화
ai_model = DietRecommendationModel()

# POST 엔드포인트: 자바 서버에서 이 주소로 데이터를 전송합니다.
@app.post("/api/recommend", response_model=DietResponse)
def recommend_diet(request: DietRequest):
    try:
        recommendations = ai_model.predict(
            ingredients=request.ingredients,
            condiments=request.condiments,
            target_calories=request.target_calories
        )
        return DietResponse(recommendations=recommendations)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# GET 엔드포인트: 서버 상태 확인용
@app.get("/api/health")
def health_check():
    return {"status": "ok", "message": "Diet Recommendation Model API is running normally."}

# 실행 방법: 터미널에서 `uvicorn main:app --reload` 입력
