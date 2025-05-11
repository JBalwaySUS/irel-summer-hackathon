from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from .handler import DietRequirementsHandler
from datetime import datetime

class UserProfileRequest(BaseModel):
    user_profile: Dict[str, Any]
    user_id: Optional[str] = None

router = APIRouter()
handler = DietRequirementsHandler()

@router.post("/requirements", status_code=status.HTTP_201_CREATED)
async def create_diet_requirements(request: UserProfileRequest):
    """
    Generate diet requirements based on user profile sent by orchestrator
    """
    # Generate diet requirements using the provided profile
    diet_requirement = await handler.generate_diet_requirements_from_profile(
        user_profile=request.user_profile,
        user_id=request.user_id
    )
    
    # Save to database
    requirement_id = await handler.save_diet_requirements(diet_requirement)
    
    # Get the saved requirement
    saved_requirement = await handler.get_diet_requirement_by_id(requirement_id)
    
    return saved_requirement

@router.get("/requirements/{requirement_id}")
async def get_diet_requirement(requirement_id: str):
    """
    Get a specific diet requirement by ID
    """
    # Get the diet requirement
    diet_requirement = await handler.get_diet_requirement_by_id(requirement_id)
    
    if not diet_requirement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diet requirement not found"
        )
    
    return diet_requirement

@router.get("/requirements/user/{user_id}/latest")
async def get_latest_diet_requirements(user_id: str):
    """
    Get the latest diet requirements for a user
    """
    # Get the latest diet requirement
    diet_requirement = await handler.get_latest_diet_requirement_for_user(user_id)
    
    if not diet_requirement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No diet requirements found for user"
        )
    
    return diet_requirement
