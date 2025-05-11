from fastapi import APIRouter, HTTPException, status
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from .models import FoodRecommendationCreate, FoodRecommendationResponse, UserDataRequest
from .handler import FoodRecommendationHandler
from typing import List, Dict, Any
from pydantic import BaseModel

router = APIRouter()
handler = FoodRecommendationHandler()

@router.post("/food-recommendation", response_model=FoodRecommendationResponse, status_code=status.HTTP_201_CREATED)
async def create_food_recommendation(request: UserDataRequest):
    """
    Generate food recommendations based on diet requirements
    """
    # Extract user ID from the user_data
    user_data = request.user_data
    user_id = user_data.get("id")
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User ID not provided in user_data"
        )
    
    # Extract diet requirement ID
    diet_requirement = request.diet_requirement
    diet_requirement_id = diet_requirement.get("id")
    
    if not diet_requirement_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Diet requirement ID not found in diet_requirement"
        )
    
    
    # Generate food recommendations
    food_recommendation = await handler.generate_food_recommendation(
        user_id=user_id,
        user_data=user_data,
        diet_requirement=diet_requirement,  # Pass full diet requirement object
        food_availability=request.food_availability,
        meal_preferences=request.meal_preferences
    )
    
    # Save to database
    recommendation_id = await handler.save_food_recommendation(food_recommendation)
    
    # Get the saved recommendation
    saved_recommendation = await handler.get_recommendation_by_id(recommendation_id)
    
    return saved_recommendation

@router.get("/food-recommendation/user/{user_id}/latest", response_model=FoodRecommendationResponse)
async def get_latest_food_recommendation(user_id: str):
    """
    Get the latest food recommendation for a user
    """
    # Get the latest food recommendation
    food_recommendation = await handler.get_latest_recommendation_for_user(user_id)
    
    if not food_recommendation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No food recommendations found for user"
        )
    
    return food_recommendation

@router.get("/food-recommendation/{recommendation_id}", response_model=FoodRecommendationResponse)
async def get_food_recommendation(recommendation_id: str):
    """
    Get a specific food recommendation by ID
    """
    # Get the food recommendation
    food_recommendation = await handler.get_recommendation_by_id(recommendation_id)
    
    if not food_recommendation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Food recommendation not found"
        )
    
    return food_recommendation