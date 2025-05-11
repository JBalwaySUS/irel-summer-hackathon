from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime
from enum import Enum

class FeedbackType(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"

class AnalysisStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"

class UserFeedback(BaseModel):
    user_id: str
    food_recommendation_id: str
    feedback_text: str
    feedback_type: FeedbackType
    created_at: datetime

class FeedbackAnalysis(BaseModel):
    feedback_id: str
    created_at: datetime
    status: AnalysisStatus = AnalysisStatus.PENDING
    identified_concerns: Optional[List[str]] = None
    suggested_restrictions: Optional[List[str]] = None
    suggested_alternatives: Optional[Dict[str, List[str]]] = None
    recommendation: Optional[str] = None
    llm_response: Optional[str] = None
    error_message: Optional[str] = None

class FeedbackCreate(BaseModel):
    food_recommendation_id: str
    feedback_text: str
    feedback_type: FeedbackType

class FeedbackResponse(BaseModel):
    id: str
    user_id: str
    food_recommendation_id: str
    feedback_text: str
    feedback_type: FeedbackType
    created_at: datetime
    analysis: Optional[Dict] = None

    class Config:
        orm_mode = True

class FeedbackAnalysisResponse(BaseModel):
    id: str
    feedback_id: str
    created_at: datetime
    status: AnalysisStatus
    identified_concerns: Optional[List[str]] = None
    suggested_restrictions: Optional[List[str]] = None
    suggested_alternatives: Optional[Dict[str, List[str]]] = None
    recommendation: Optional[str] = None

    class Config:
        orm_mode = True