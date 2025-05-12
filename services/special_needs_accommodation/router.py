from fastapi import APIRouter, HTTPException, status
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from .models import FeedbackCreate, FeedbackResponse, FeedbackAnalysisResponse, UserFeedback, FeedbackType
from .handler import SpecialNeedsHandler
from datetime import datetime
from typing import List, Dict, Any

router = APIRouter()
handler = SpecialNeedsHandler()

@router.post("/feedback", response_model=FeedbackResponse)
async def create_feedback(feedback_data: Dict[str, Any]):
    """
    Submit feedback about a food recommendation
    """
    user_id = feedback_data["user_data"]["id"]
    
    # Create feedback object
    feedback = UserFeedback(
        user_id=user_id,
        food_recommendation_id=feedback_data["food_recommendation_id"],
        feedback_text=feedback_data["feedback_text"],
        feedback_type=feedback_data["feedback_type"],
        created_at=datetime.utcnow()
    )
    
    # Save feedback to database
    feedback_id = await handler.save_feedback(feedback)
    
    # If feedback is negative, analyze it
    if feedback.feedback_type == FeedbackType.NEGATIVE:
        # Extract data passed from frontend
        food_recommendation = feedback_data.get("food_recommendation", {})
        user_profile = feedback_data.get("user_data", {}).get("profile", {})
        
        analysis = await handler.analyze_feedback(
            feedback_id=feedback_id,
            food_recommendation=food_recommendation,
            user_profile=user_profile
        )
        analysis_id = await handler.save_analysis(analysis)
    
    # Get the saved feedback
    saved_feedback = await handler.get_feedback_by_id(feedback_id)
    
    return saved_feedback

@router.get("/feedback/user/{user_id}", response_model=List[FeedbackResponse])
async def get_user_feedbacks(user_id: str):
    """
    Get all feedbacks for the specified user
    """
    # Get feedbacks
    feedbacks = await handler.get_user_feedbacks(user_id)
    
    return feedbacks

@router.get("/feedback/{feedback_id}", response_model=FeedbackResponse)
async def get_feedback(feedback_id: str):
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
    
    return feedback

@router.get("/analysis/{analysis_id}", response_model=FeedbackAnalysisResponse)
async def get_analysis(analysis_id: str):
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
    
    return analysis

@router.post("/special-needs-plan", status_code=status.HTTP_201_CREATED)
async def create_special_needs_plan(plan_data: Dict[str, Any]):
    """
    Generate and save a special needs accommodation plan
    """
    user_id = None
    if "user_data" in plan_data:
        user_id = plan_data["user_data"].get("id")
    
    # Generate plan
    plan = await handler.generate_plan_from_data(
        user_profile=plan_data.get("user_profile", {}),
        food_recommendation=plan_data.get("food_recommendation", {}),
        user_id=user_id
    )
    
    # Save plan to database
    plan_id = await handler.save_plan(plan)
    
    # Get the saved plan
    saved_plan = await handler.get_plan_by_id(plan_id)
    
    return saved_plan

@router.get("/special-needs-plan/{plan_id}")
async def get_special_needs_plan(plan_id: str):
    """
    Get a specific special needs plan by ID
    """
    plan = await handler.get_plan_by_id(plan_id)
    
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Special needs plan not found"
        )
    
    return plan

@router.get("/special-needs-plan/user/{user_id}/latest")
async def get_latest_special_needs_plan(user_id: str):
    """
    Get the latest special needs plan for a user
    """
    plan = await handler.get_latest_plan_for_user(user_id)
    
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No special needs plan found for this user"
        )
    
    return plan