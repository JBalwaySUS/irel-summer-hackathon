from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

# Assuming similar structure as diet requirements service
class FoodRecommendationRequest(BaseModel):
    user_profile: Dict[str, Any]
    diet_requirements: Dict[str, Any]
    user_id: Optional[str] = None

router = APIRouter()

@router.post("/recommendations", status_code=status.HTTP_201_CREATED)
async def create_food_recommendation(request: FoodRecommendationRequest):
    """
    Generate food recommendations based on user profile and diet requirements sent by orchestrator
    """
    # You'll need to implement a handler method that accepts the profile and diet requirements
    # For now, this is a placeholder for the implementation
    from services.food_plate_recommendation.handler import FoodRecommendationHandler
    handler = FoodRecommendationHandler()
    
    # Generate recommendations
    recommendations = await handler.generate_recommendations_from_data(
        user_profile=request.user_profile,
        diet_requirements=request.diet_requirements,
        user_id=request.user_id
    )
    
    # Save to database
    recommendation_id = await handler.save_recommendations(recommendations)
    
    # Get the saved recommendation
    saved_recommendation = await handler.get_recommendation_by_id(recommendation_id)
    
    return saved_recommendation

@router.get("/recommendations/{recommendation_id}")
async def get_food_recommendation(recommendation_id: str):
    """
    Get a specific food recommendation by ID
    """
    from services.food_plate_recommendation.handler import FoodRecommendationHandler
    handler = FoodRecommendationHandler()
    
    # Get the recommendation
    recommendation = await handler.get_recommendation_by_id(recommendation_id)
    
    if not recommendation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Food recommendation not found"
        )
    
    return recommendation

@router.get("/recommendations/user/{user_id}/latest")
async def get_latest_food_recommendation(user_id: str):
    """
    Get the latest food recommendation for a user
    """
    from services.food_plate_recommendation.handler import FoodRecommendationHandler
    handler = FoodRecommendationHandler()
    
    # Get the latest recommendation
    recommendation = await handler.get_latest_recommendation_for_user(user_id)
    
    if not recommendation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No food recommendations found for user"
        )
    
    return recommendation
