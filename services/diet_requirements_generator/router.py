from fastapi import APIRouter, HTTPException, Depends, status
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from services.user_management.auth import get_current_user
from .models import DietRequirementCreate, DietRequirementResponse
from .handler import DietRequirementsHandler
from typing import List

router = APIRouter()
handler = DietRequirementsHandler()

@router.post("/diet-requirements", response_model=DietRequirementResponse, status_code=status.HTTP_201_CREATED)
async def create_diet_requirements(current_user=Depends(get_current_user)):
    """
    Generate diet requirements for the current user
    """
    user_id = current_user["id"]
    
    # Generate diet requirements
    diet_requirement = await handler.generate_diet_requirements(user_id)
    
    # Save to database
    requirement_id = await handler.save_diet_requirements(diet_requirement)
    
    # Get the saved requirement
    saved_requirement = await handler.get_diet_requirement_by_id(requirement_id)
    
    return saved_requirement

@router.get("/diet-requirements/latest", response_model=DietRequirementResponse)
async def get_latest_diet_requirements(current_user=Depends(get_current_user)):
    """
    Get the latest diet requirements for the current user
    """
    user_id = current_user["id"]
    
    # Get the latest diet requirement
    diet_requirement = await handler.get_latest_diet_requirement_for_user(user_id)
    
    if not diet_requirement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No diet requirements found for user"
        )
    
    return diet_requirement

@router.get("/diet-requirements/{requirement_id}", response_model=DietRequirementResponse)
async def get_diet_requirement(requirement_id: str, current_user=Depends(get_current_user)):
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
    
    # Verify that the requirement belongs to the current user
    if diet_requirement["user_id"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this diet requirement"
        )
    
    return diet_requirement