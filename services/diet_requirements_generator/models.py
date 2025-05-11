from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime
from enum import Enum

class DietRequirementStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"

class NutritionalValue(BaseModel):
    calories: float
    protein: float  # in grams
    carbohydrates: float  # in grams
    fat: float  # in grams
    fiber: float  # in grams
    sugar: Optional[float] = None  # in grams
    sodium: Optional[float] = None  # in milligrams
    vitamins: Optional[Dict[str, float]] = None  # key-value pairs for different vitamins

class DietRequirement(BaseModel):
    user_id: str
    created_at: datetime
    status: DietRequirementStatus = DietRequirementStatus.PENDING
    daily_requirements: Optional[Dict[str, NutritionalValue]] = None  # key is day of week
    weekly_average: Optional[NutritionalValue] = None
    llm_response: Optional[str] = None
    error_message: Optional[str] = None

class DietRequirementCreate(BaseModel):
    user_id: str

class DietRequirementResponse(BaseModel):
    id: str
    user_id: str
    created_at: datetime
    status: DietRequirementStatus
    daily_requirements: Optional[Dict[str, NutritionalValue]] = None
    weekly_average: Optional[NutritionalValue] = None

    class Config:
        orm_mode = True