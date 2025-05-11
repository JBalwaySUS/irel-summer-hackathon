import sys
import os
import json
from datetime import datetime
from typing import Dict, Any, Optional
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from services.shared.llm_client import LLMClient
from services.shared.database import get_user_collection, get_diet_plan_collection, get_food_recommendation_collection
from bson import ObjectId
from .models import (
    FoodRecommendation, RecommendationStatus, 
    DailyMealPlan, Meal, FoodItem, MealType
)

class FoodRecommendationHandler:
    def __init__(self):
        self.llm_client = LLMClient()
    
    async def generate_recommendations_from_data(
        self, 
        user_profile: Dict[str, Any], 
        diet_requirements: Dict[str, Any], 
        user_id: Optional[str] = None,
        food_availability: list = None,
        meal_preferences: dict = None
    ):
        """
        Generate food recommendations based on user profile and diet requirements provided by the orchestrator
        """
        try:
            # Validate inputs
            if not user_profile:
                return {
                    "user_id": user_id,
                    "created_at": datetime.utcnow(),
                    "status": "FAILED",
                    "error_message": "User profile data not provided"
                }
                
            if not diet_requirements:
                return {
                    "user_id": user_id,
                    "created_at": datetime.utcnow(),
                    "status": "FAILED",
                    "error_message": "Diet requirements data not provided"
                }
            
            # Extract relevant profile data
            age = user_profile["age"]
            gender = user_profile["gender"]
            height = user_profile["height"]
            weight = user_profile["weight"]
            diet_type = user_profile["diet_type"]
            activity_level = user_profile["activity_level"]
            health_goal = user_profile["health_goal"]
            allergies = user_profile.get("allergies", [])
            dietary_restrictions = user_profile.get("dietary_restrictions", [])
            medical_conditions = user_profile.get("medical_conditions", [])
            
            # Extract diet requirements data
            weekly_average = diet_requirements.get("weekly_average", {})
            daily_requirements = diet_requirements.get("daily_requirements", {})
            
            # Create system prompt for food recommendation
            system_prompt = """
You are a professional nutritionist who specializes in creating personalized meal plans.
Your task is to generate a weekly meal plan based on a person's profile and their nutritional requirements.
Generate a meal plan for each day of the week with breakfast, lunch, dinner, and snacks.
The response should be structured as a JSON object.

Only respond with the JSON object, no additional text.
            """
            
            # Create user prompt with profile and requirements information
            user_prompt = f"""
Generate a weekly meal plan for a person with the following profile:
- Age: {age}
- Gender: {gender}
- Height: {height} cm
- Weight: {weight} kg
- Diet type: {diet_type}
- Activity level: {activity_level}
- Health goal: {health_goal}
- Allergies: {', '.join(allergies) if allergies else 'None'}
- Dietary restrictions: {', '.join(dietary_restrictions) if dietary_restrictions else 'None'}
- Medical conditions: {', '.join(medical_conditions) if medical_conditions else 'None'}

The nutritional requirements are:
{json.dumps(weekly_average, indent=2)}

Please provide a detailed meal plan for each day of the week (Monday through Sunday) that matches these requirements.
Each day should include breakfast, lunch, dinner, and 1-2 snacks.
For each meal, include a brief description, ingredients, and preparation instructions.
"""
            
            # Call LLM API to generate food recommendations
            llm_response = await self.llm_client.generate_response(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.3
            )
            
            if not llm_response:
                return {
                    "user_id": user_id,
                    "created_at": datetime.utcnow(),
                    "status": "FAILED",
                    "error_message": "Failed to generate response from LLM"
                }
            
            # Parse the JSON response
            try:
                food_recommendation_data = json.loads(llm_response)
                
                # Create and return the food recommendation object
                return {
                    "user_id": user_id,
                    "created_at": datetime.utcnow(),
                    "status": "COMPLETED",
                    "weekly_plan": food_recommendation_data,
                    "llm_response": llm_response
                }
            except json.JSONDecodeError as e:
                return {
                    "user_id": user_id,
                    "created_at": datetime.utcnow(),
                    "status": "FAILED",
                    "error_message": f"Failed to parse LLM response as JSON: {str(e)}",
                    "llm_response": llm_response
                }
            except Exception as e:
                return {
                    "user_id": user_id,
                    "created_at": datetime.utcnow(),
                    "status": "FAILED",
                    "error_message": f"Error processing LLM response: {str(e)}",
                    "llm_response": llm_response
                }
                
        except Exception as e:
            return {
                "user_id": user_id,
                "created_at": datetime.utcnow(),
                "status": "FAILED",
                "error_message": f"Error generating food recommendations: {str(e)}"
            }
    
    # Keep the original method for backward compatibility
    async def generate_food_recommendation(
        self, 
        user_id: str, 
        diet_requirement_id: str,
        food_availability: list = None,
        meal_preferences: dict = None
    ) -> FoodRecommendation:
        """
        Generate food recommendations based on diet requirements
        """
        try:
            # Get diet requirements
            diet_plan_collection = await get_diet_plan_collection()
            diet_requirement = await diet_plan_collection.find_one({"_id": ObjectId(diet_requirement_id)})
            
            if not diet_requirement:
                return FoodRecommendation(
                    user_id=user_id,
                    diet_requirement_id=diet_requirement_id,
                    created_at=datetime.utcnow(),
                    status=RecommendationStatus.FAILED,
                    error_message="Diet requirement not found"
                )
            
            # Get user profile
            user_collection = await get_user_collection()
            user = await user_collection.find_one({"_id": ObjectId(user_id)})
            
            if not user or not user.get("profile"):
                return FoodRecommendation(
                    user_id=user_id,
                    diet_requirement_id=diet_requirement_id,
                    created_at=datetime.utcnow(),
                    status=RecommendationStatus.FAILED,
                    error_message="User profile not found"
                )
            
            # Extract profile data
            profile = user["profile"]
            diet_type = profile["diet_type"]
            allergies = profile.get("allergies", [])
            dietary_restrictions = profile.get("dietary_restrictions", [])
            
            # Create system prompt
            system_prompt = f"""
You are a professional nutritionist who specializes in creating personalized meal plans.
Your task is to generate daily meal plans for a person based on their nutritional requirements and dietary preferences.
Generate meal plans for each day of the week (breakfast, lunch, dinner, and optional snacks).
The response should be structured as a JSON object with the following format:

{{
  "meal_plans": {{
    "monday": {{
      "day": "monday",
      "meals": [
        {{
          "meal_type": "breakfast",
          "food_items": [
            {{
              "name": string,
              "quantity": string,
              "calories": float,
              "protein": float,
              "carbohydrates": float,
              "fat": float,
              "fiber": float,
              "preparation_notes": string (optional)
            }},
            ...
          ],
          "total_calories": float,
          "total_protein": float,
          "total_carbohydrates": float,
          "total_fat": float,
          "total_fiber": float,
          "notes": string (optional)
        }},
        {{
          "meal_type": "lunch",
          ...
        }},
        {{
          "meal_type": "dinner",
          ...
        }},
        {{
          "meal_type": "snack",
          ...
        }}
      ],
      "total_calories": float,
      "total_protein": float,
      "total_carbohydrates": float,
      "total_fat": float,
      "total_fiber": float,
      "notes": string (optional)
    }},
    "tuesday": {{ ... }},
    ...
    "sunday": {{ ... }}
  }},
  "additional_notes": string (optional)
}}

Ensure the meal plans meet the nutritional requirements for each day.
Make the meals realistic, varied, practical, and aligned with the person's dietary preferences.
Provide specific quantities for each food item (e.g., "2 tbsp", "100g", "1 cup").
Include preparation notes for complex items where helpful.
Only respond with the JSON object, no additional text.
"""
            
            # Create user prompt with nutritional requirements and preferences
            user_prompt = f"""
Generate meal plans for a person with the following profile:
- Diet type: {diet_type}
- Allergies: {', '.join(allergies) if allergies else 'None'}
- Dietary restrictions: {', '.join(dietary_restrictions) if dietary_restrictions else 'None'}

Daily nutritional requirements:
"""
            
            # Add daily nutritional requirements to the prompt
            for day, values in diet_requirement["daily_requirements"].items():
                user_prompt += f"\n{day.capitalize()}:\n"
                user_prompt += f"- Calories: {values['calories']:.1f} kcal\n"
                user_prompt += f"- Protein: {values['protein']:.1f} g\n"
                user_prompt += f"- Carbohydrates: {values['carbohydrates']:.1f} g\n"
                user_prompt += f"- Fat: {values['fat']:.1f} g\n"
                user_prompt += f"- Fiber: {values['fiber']:.1f} g\n"
            
            # Add food availability constraints if provided
            if food_availability:
                user_prompt += f"\nFood availability constraints (only use these foods):\n"
                for food in food_availability:
                    user_prompt += f"- {food}\n"
            
            # Add meal preferences if provided
            if meal_preferences:
                user_prompt += f"\nMeal preferences:\n"
                for meal_type, preferences in meal_preferences.items():
                    user_prompt += f"- {meal_type.capitalize()}: {', '.join(preferences)}\n"
            
            # Call LLM API to generate meal recommendations
            llm_response = await self.llm_client.generate_response(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.5
            )
            
            if not llm_response:
                return FoodRecommendation(
                    user_id=user_id,
                    diet_requirement_id=diet_requirement_id,
                    created_at=datetime.utcnow(),
                    status=RecommendationStatus.FAILED,
                    error_message="Failed to generate response from LLM"
                )
            
            # Parse the JSON response
            try:
                recommendation_data = json.loads(llm_response)
                
                # Convert the data to Pydantic models
                meal_plans = {}
                for day, plan_data in recommendation_data["meal_plans"].items():
                    # Process meals
                    meals = []
                    for meal_data in plan_data["meals"]:
                        # Process food items
                        food_items = []
                        for item_data in meal_data["food_items"]:
                            food_items.append(FoodItem(**item_data))
                        
                        meals.append(Meal(
                            meal_type=meal_data["meal_type"],
                            food_items=food_items,
                            total_calories=meal_data["total_calories"],
                            total_protein=meal_data["total_protein"],
                            total_carbohydrates=meal_data["total_carbohydrates"],
                            total_fat=meal_data["total_fat"],
                            total_fiber=meal_data["total_fiber"],
                            notes=meal_data.get("notes")
                        ))
                    
                    meal_plans[day] = DailyMealPlan(
                        day=plan_data["day"],
                        meals=meals,
                        total_calories=plan_data["total_calories"],
                        total_protein=plan_data["total_protein"],
                        total_carbohydrates=plan_data["total_carbohydrates"],
                        total_fat=plan_data["total_fat"],
                        total_fiber=plan_data["total_fiber"],
                        notes=plan_data.get("notes")
                    )
                
                # Create and return the food recommendation object
                return FoodRecommendation(
                    user_id=user_id,
                    diet_requirement_id=diet_requirement_id,
                    created_at=datetime.utcnow(),
                    status=RecommendationStatus.COMPLETED,
                    meal_plans=meal_plans,
                    additional_notes=recommendation_data.get("additional_notes"),
                    llm_response=llm_response
                )
            except json.JSONDecodeError as e:
                return FoodRecommendation(
                    user_id=user_id,
                    diet_requirement_id=diet_requirement_id,
                    created_at=datetime.utcnow(),
                    status=RecommendationStatus.FAILED,
                    error_message=f"Failed to parse LLM response as JSON: {str(e)}",
                    llm_response=llm_response
                )
            except Exception as e:
                return FoodRecommendation(
                    user_id=user_id,
                    diet_requirement_id=diet_requirement_id,
                    created_at=datetime.utcnow(),
                    status=RecommendationStatus.FAILED,
                    error_message=f"Error processing LLM response: {str(e)}",
                    llm_response=llm_response
                )
                
        except Exception as e:
            return FoodRecommendation(
                user_id=user_id,
                diet_requirement_id=diet_requirement_id,
                created_at=datetime.utcnow(),
                status=RecommendationStatus.FAILED,
                error_message=f"Error generating food recommendations: {str(e)}"
            )
    
    async def save_food_recommendation(self, recommendation: FoodRecommendation):
        """
        Save food recommendation to database
        """
        food_recommendation_collection = await get_food_recommendation_collection()
        
        # Convert Pydantic model to dict
        recommendation_dict = recommendation.dict()
        
        # Insert into database
        result = await food_recommendation_collection.insert_one(recommendation_dict)
        
        # Return the ID of the inserted document
        return str(result.inserted_id)
    
    async def get_recommendation_by_id(self, recommendation_id: str):
        """
        Get food recommendation by ID
        """
        food_recommendation_collection = await get_food_recommendation_collection()
        recommendation = await food_recommendation_collection.find_one({"_id": ObjectId(recommendation_id)})
        
        if recommendation:
            recommendation["id"] = str(recommendation.pop("_id"))
            return recommendation
        
        return None
    
    async def get_latest_recommendation_for_user(self, user_id: str):
        """
        Get the latest food recommendation for a user
        """
        food_recommendation_collection = await get_food_recommendation_collection()
        recommendations = await food_recommendation_collection.find(
            {"user_id": user_id}
        ).sort("created_at", -1).limit(1).to_list(length=1)
        
        if recommendations:
            recommendation = recommendations[0]
            recommendation["id"] = str(recommendation.pop("_id"))
            return recommendation
        
        return None