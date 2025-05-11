from fastapi import APIRouter, HTTPException, Depends, status
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from services.user_management.auth import get_current_user
from .models import FoodRecommendationCreate, FoodRecommendationResponse
from .handler import FoodRecommendationHandler
from typing import List

router = APIRouter()
handler = FoodRecommendationHandler()

@router.post("/food-recommendations", response_model=FoodRecommendationResponse, status_code=status.HTTP_201_CREATED)
async def create_food_recommendation(
    recommendation_data: FoodRecommendationCreate,
    current_user=Depends(get_current_user)
):
    """
    Generate food recommendations based on diet requirements
    """
    user_id = current_user["id"]
    
    # Generate food recommendations
    food_recommendation = await handler.generate_food_recommendation(
        user_id=user_id,
        diet_requirement_id=recommendation_data.diet_requirement_id,
        food_availability=recommendation_data.food_availability,
        meal_preferences=recommendation_data.meal_preferences
    )
    
    # Save to database
    recommendation_id = await handler.save_food_recommendation(food_recommendation)
    
    # Get the saved recommendation
    saved_recommendation = await handler.get_recommendation_by_id(recommendation_id)
    
    return saved_recommendation

@router.get("/food-recommendations/latest", response_model=FoodRecommendationResponse)
async def get_latest_food_recommendation(current_user=Depends(get_current_user)):
    """
    Get the latest food recommendation for the current user
    """
    user_id = current_user["id"]
    
    # Get the latest food recommendation
    food_recommendation = await handler.get_latest_recommendation_for_user(user_id)
    
    if not food_recommendation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No food recommendations found for user"
        )
    
    return food_recommendation

@router.get("/food-recommendations/{recommendation_id}", response_model=FoodRecommendationResponse)
async def get_food_recommendation(recommendation_id: str, current_user=Depends(get_current_user)):
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
    
    # Verify that the recommendation belongs to the current user
    if food_recommendation["user_id"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this food recommendation"
        )
    
    return food_recommendation