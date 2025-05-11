from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class RecommendationStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"

class MealType(str, Enum):
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"

class FoodItem(BaseModel):
    name: str
    quantity: str
    calories: float
    protein: float
    carbohydrates: float
    fat: float
    fiber: float
    preparation_notes: Optional[str] = None

class Meal(BaseModel):
    meal_type: MealType
    food_items: List[FoodItem]
    total_calories: float
    total_protein: float
    total_carbohydrates: float
    total_fat: float
    total_fiber: float
    notes: Optional[str] = None

class DailyMealPlan(BaseModel):
    day: str  # monday, tuesday, etc.
    meals: List[Meal]
    total_calories: float
    total_protein: float
    total_carbohydrates: float
    total_fat: float
    total_fiber: float
    notes: Optional[str] = None

class FoodRecommendation(BaseModel):
    user_id: str
    diet_requirement_id: str
    created_at: datetime
    status: RecommendationStatus = RecommendationStatus.PENDING
    meal_plans: Optional[Dict[str, DailyMealPlan]] = None
    additional_notes: Optional[str] = None
    llm_response: Optional[str] = None
    error_message: Optional[str] = None

class FoodRecommendationCreate(BaseModel):
    diet_requirement_id: str
    food_availability: Optional[List[str]] = None
    meal_preferences: Optional[Dict[str, List[str]]] = None

class FoodRecommendationResponse(BaseModel):
    id: str
    user_id: str
    diet_requirement_id: str
    created_at: datetime
    status: RecommendationStatus
    meal_plans: Optional[Dict[str, DailyMealPlan]] = None
    additional_notes: Optional[str] = None

    class Config:
        orm_mode = True

class UserDataRequest(BaseModel):
    user_data: Dict[str, Any]
    diet_requirement: Dict[str, Any]
    food_availability: Optional[List[str]] = None
    meal_preferences: Optional[Dict[str, List[str]]] = None