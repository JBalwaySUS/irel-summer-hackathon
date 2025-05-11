from fastapi import APIRouter, HTTPException, Depends, status
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from services.user_management.auth import get_current_user
from .models import FeedbackCreate, FeedbackResponse, FeedbackAnalysisResponse, UserFeedback, FeedbackType
from .handler import SpecialNeedsHandler
from datetime import datetime
from typing import List

router = APIRouter()
handler = SpecialNeedsHandler()

@router.post("/feedback", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def create_feedback(
    feedback_data: FeedbackCreate,
    current_user=Depends(get_current_user)
):
    """
    Submit feedback about a food recommendation
    """
    user_id = current_user["id"]
    
    # Create feedback object
    feedback = UserFeedback(
        user_id=user_id,
        food_recommendation_id=feedback_data.food_recommendation_id,
        feedback_text=feedback_data.feedback_text,
        feedback_type=feedback_data.feedback_type,
        created_at=datetime.utcnow()
    )
    
    # Save feedback to database
    feedback_id = await handler.save_feedback(feedback)
    
    # If feedback is negative, analyze it
    if feedback.feedback_type == FeedbackType.NEGATIVE:
        analysis = await handler.analyze_feedback(feedback_id)
        analysis_id = await handler.save_analysis(analysis)
    
    # Get the saved feedback
    saved_feedback = await handler.get_feedback_by_id(feedback_id)
    
    return saved_feedback

@router.get("/feedback", response_model=List[FeedbackResponse])
async def get_user_feedbacks(current_user=Depends(get_current_user)):
    """
    Get all feedbacks for the current user
    """
    user_id = current_user["id"]
    
    # Get feedbacks
    feedbacks = await handler.get_user_feedbacks(user_id)
    
    return feedbacks

@router.get("/feedback/{feedback_id}", response_model=FeedbackResponse)
async def get_feedback(feedback_id: str, current_user=Depends(get_current_user)):
    """
    Get a specific feedback by ID
    """
    # Get the feedback
    feedback = await handler.get_feedback_by_id(feedback_id)
    
    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback not found"
        )
    
    # Verify that the feedback belongs to the current user
    if feedback["user_id"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this feedback"
        )
    
    return feedback

@router.get("/analysis/{analysis_id}", response_model=FeedbackAnalysisResponse)
async def get_analysis(analysis_id: str, current_user=Depends(get_current_user)):
    """
    Get a specific feedback analysis by ID
    """
    # Get the analysis
    analysis = await handler.get_analysis_by_id(analysis_id)
    
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found"
        )
    
    # Get the feedback to verify ownership
    feedback = await handler.get_feedback_by_id(analysis["feedback_id"])
    
    if not feedback or feedback["user_id"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this analysis"
        )
    
    return analysis