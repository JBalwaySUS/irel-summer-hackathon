from fastapi import APIRouter, HTTPException, status
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from .models import DietRequirementCreate, DietRequirementResponse
from .handler import DietRequirementsHandler
from typing import List, Dict, Any
from pydantic import BaseModel

# Define request models for the unprotected API
class UserDataRequest(BaseModel):
    user_data: Dict[str, Any]

router = APIRouter()
handler = DietRequirementsHandler()

@router.post("/diet-requirements", response_model=DietRequirementResponse, status_code=status.HTTP_201_CREATED)
async def create_diet_requirements(request: UserDataRequest):
    """
    Generate diet requirements based on user profile data sent from frontend
    """
    # Extract user profile and ID from the user_data
    user_data = request.user_data
    user_profile = user_data.get("profile")
    user_id = user_data.get("id")
    
    if not user_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User profile data not provided"
        )
    
    # Generate diet requirements
    diet_requirement = await handler.generate_diet_requirements_from_profile(
        user_profile=user_profile,
        user_id=user_id
    )
    
    if not diet_requirement:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate diet requirements"
        )
    
    # Save and get the ID
    requirement_id = await handler.save_diet_requirements(diet_requirement)

    if not requirement_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save generated diet requirements"
        )
    
    # Create a properly formatted response object
    response = DietRequirementResponse(
        status_code=status.HTTP_201_CREATED,
        id=requirement_id,
        user_id=diet_requirement.user_id,
        created_at=diet_requirement.created_at,
        status=diet_requirement.status,
        daily_requirements=diet_requirement.daily_requirements,
        weekly_average=diet_requirement.weekly_average
    )
    
    return response

@router.get("/diet-requirements/user/{user_id}/latest", response_model=DietRequirementResponse)
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

@router.get("/diet-requirements/{requirement_id}", response_model=DietRequirementResponse)
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