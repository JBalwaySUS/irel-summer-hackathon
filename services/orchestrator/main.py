import asyncio
import uvicorn
from fastapi import FastAPI, HTTPException
import httpx
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import os

app = FastAPI()

# Service endpoints
USER_MANAGEMENT_URL = "http://user-management:8000"
DIET_REQUIREMENTS_URL = "http://diet-requirements:8001"
FOOD_RECOMMENDATION_URL = "http://food-recommendation:8002"
SPECIAL_NEEDS_URL = "http://special-needs:8003"

# Client for making HTTP requests
client = httpx.AsyncClient(timeout=60.0)

class UserResponse(BaseModel):
    id: str
    profile: Dict[str, Any]

class DietRequirementRequest(BaseModel):
    user_profile: Dict[str, Any]

class FoodRecommendationRequest(BaseModel):
    user_profile: Dict[str, Any]
    diet_requirements: Dict[str, Any]

class SpecialNeedsRequest(BaseModel):
    user_profile: Dict[str, Any]
    food_recommendation: Dict[str, Any]

@app.get("/")
async def root():
    return {"message": "Orchestrator Service API"}

@app.get("/health")
async def health_check():
    return {"status": "OK"}

@app.get("/users/{user_id}")
async def get_user(user_id: str):
    """Get user details from user management service"""
    try:
        response = await client.get(f"{USER_MANAGEMENT_URL}/users/{user_id}")
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting user: {str(e)}")

@app.post("/diet-requirements/{user_id}")
async def generate_diet_requirements(user_id: str):
    """Orchestrate diet requirements generation"""
    try:
        # Get user data
        user_data = await get_user(user_id)
        
        # Send only the necessary profile data to the diet requirements service
        request_data = DietRequirementRequest(user_profile=user_data["profile"])
        
        # Generate diet requirements
        response = await client.post(
            f"{DIET_REQUIREMENTS_URL}/requirements",
            json=request_data.dict()
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating diet requirements: {str(e)}")

@app.post("/food-recommendation/{user_id}")
async def generate_food_recommendation(user_id: str, diet_requirement_id: Optional[str] = None):
    """Orchestrate food recommendation generation"""
    try:
        # Get user data
        user_data = await get_user(user_id)
        
        # If diet_requirement_id is not provided, generate new diet requirements
        if not diet_requirement_id:
            diet_req_response = await generate_diet_requirements(user_id)
            diet_requirement_id = diet_req_response["id"]
        
        # Get the diet requirement data
        diet_req_response = await client.get(f"{DIET_REQUIREMENTS_URL}/requirements/{diet_requirement_id}")
        diet_req_response.raise_for_status()
        diet_requirements = diet_req_response.json()
        
        # Send request to food recommendation service
        request_data = FoodRecommendationRequest(
            user_profile=user_data["profile"],
            diet_requirements=diet_requirements
        )
        
        response = await client.post(
            f"{FOOD_RECOMMENDATION_URL}/recommendations",
            json=request_data.dict()
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating food recommendation: {str(e)}")

@app.post("/special-needs/{user_id}")
async def accommodate_special_needs(user_id: str, food_recommendation_id: Optional[str] = None):
    """Orchestrate special needs accommodation"""
    try:
        # Get user data
        user_data = await get_user(user_id)
        
        # If food_recommendation_id is not provided, generate new food recommendation
        if not food_recommendation_id:
            food_rec_response = await generate_food_recommendation(user_id)
            food_recommendation_id = food_rec_response["id"]
        
        # Get the food recommendation data
        food_rec_response = await client.get(f"{FOOD_RECOMMENDATION_URL}/recommendations/{food_recommendation_id}")
        food_rec_response.raise_for_status()
        food_recommendation = food_rec_response.json()
        
        # Send request to special needs service
        request_data = SpecialNeedsRequest(
            user_profile=user_data["profile"],
            food_recommendation=food_recommendation
        )
        
        response = await client.post(
            f"{SPECIAL_NEEDS_URL}/accommodate",
            json=request_data.dict()
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error accommodating special needs: {str(e)}")

@app.get("/full-plan/{user_id}")
async def generate_full_plan(user_id: str):
    """Generate a complete plan from user data to special needs accommodation"""
    try:
        # Start the pipeline
        special_needs_response = await accommodate_special_needs(user_id)
        
        # Return the complete plan
        return {
            "user_id": user_id,
            "special_needs_plan": special_needs_response
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating full plan: {str(e)}")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8004, reload=True)
