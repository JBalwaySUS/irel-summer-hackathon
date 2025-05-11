from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

# Request model
class SpecialNeedsRequest(BaseModel):
    user_profile: Dict[str, Any]
    food_recommendation: Dict[str, Any]
    user_id: Optional[str] = None

router = APIRouter()

@router.post("/accommodate", status_code=status.HTTP_201_CREATED)
async def create_special_needs_plan(request: SpecialNeedsRequest):
    """
    Generate special needs accommodation based on user profile and food recommendations
    """
    # You'll need to implement a handler method that accepts the profile and food recommendations
    # For now, this is a placeholder for the implementation
    from services.special_needs_accommodation.handler import SpecialNeedsHandler
    handler = SpecialNeedsHandler()
    
    # Generate special needs plan
    special_needs_plan = await handler.generate_plan_from_data(
        user_profile=request.user_profile,
        food_recommendation=request.food_recommendation,
        user_id=request.user_id
    )
    
    # Save to database
    plan_id = await handler.save_plan(special_needs_plan)
    
    # Get the saved plan
    saved_plan = await handler.get_plan_by_id(plan_id)
    
    return saved_plan

@router.get("/plans/{plan_id}")
async def get_special_needs_plan(plan_id: str):
    """
    Get a specific special needs plan by ID
    """
    from services.special_needs_accommodation.handler import SpecialNeedsHandler
    handler = SpecialNeedsHandler()
    
    # Get the plan
    plan = await handler.get_plan_by_id(plan_id)
    
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Special needs plan not found"
        )
    
    return plan

@router.get("/plans/user/{user_id}/latest")
async def get_latest_special_needs_plan(user_id: str):
    """
    Get the latest special needs plan for a user
    """
    from services.special_needs_accommodation.handler import SpecialNeedsHandler
    handler = SpecialNeedsHandler()
    
    # Get the latest plan
    plan = await handler.get_latest_plan_for_user(user_id)
    
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No special needs plans found for user"
        )
    
    return plan
