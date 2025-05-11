from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from enum import Enum
from datetime import datetime


class DietType(str, Enum):
    NON_VEGETARIAN = "non-vegetarian"
    VEGETARIAN = "vegetarian"
    VEGAN = "vegan"


class ActivityLevel(str, Enum):
    SEDENTARY = "sedentary"
    LIGHT = "light"
    MODERATE = "moderate"
    ACTIVE = "active"
    VERY_ACTIVE = "very-active"


class HealthGoal(str, Enum):
    WEIGHT_LOSS = "weight-loss"
    WEIGHT_GAIN = "weight-gain"
    MAINTENANCE = "maintenance"
    MUSCLE_GAIN = "muscle-gain"
    GENERAL_HEALTH = "general-health"


class UserBase(BaseModel):
    email: EmailStr
    name: str
    

class UserCreate(UserBase):
    password: str
    

class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserProfile(BaseModel):
    age: int = Field(..., gt=0, lt=120)
    gender: str
    height: float = Field(..., gt=0)  # in cm
    weight: float = Field(..., gt=0)  # in kg
    diet_type: DietType
    activity_level: ActivityLevel
    health_goal: HealthGoal
    allergies: List[str] = []
    dietary_restrictions: List[str] = []
    medical_conditions: List[str] = []


class UserProfileUpdate(BaseModel):
    age: Optional[int] = Field(None, gt=0, lt=120)
    gender: Optional[str] = None
    height: Optional[float] = Field(None, gt=0)  # in cm
    weight: Optional[float] = Field(None, gt=0)  # in kg
    diet_type: Optional[DietType] = None
    activity_level: Optional[ActivityLevel] = None
    health_goal: Optional[HealthGoal] = None
    allergies: Optional[List[str]] = None
    dietary_restrictions: Optional[List[str]] = None
    medical_conditions: Optional[List[str]] = None


class User(UserBase):
    id: str
    profile: Optional[UserProfile] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True