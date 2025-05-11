import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from services.shared.llm_client import LLMClient
from services.shared.database import get_diet_plan_collection
import json
from datetime import datetime
from .models import DietRequirement, DietRequirementStatus, NutritionalValue
from bson import ObjectId
from typing import Dict, Any

class DietRequirementsHandler:
    def __init__(self):
        self.llm_client = LLMClient()
    
    async def generate_diet_requirements_from_profile(self, user_profile: Dict[str, Any], user_id: str = None) -> DietRequirement:
        """
        Generate diet requirements based on user profile data provided by the orchestrator
        """
        try:
            # Validate user profile data
            if not user_profile:
                return DietRequirement(
                    user_id=user_id,
                    created_at=datetime.utcnow(),
                    status=DietRequirementStatus.FAILED,
                    error_message="User profile data not provided"
                )
            
            # Use the profile data directly
            profile = user_profile
            age = profile["age"]
            gender = profile["gender"]
            height = profile["height"]
            weight = profile["weight"]
            diet_type = profile["diet_type"]
            activity_level = profile["activity_level"]
            health_goal = profile["health_goal"]
            allergies = profile.get("allergies", [])
            dietary_restrictions = profile.get("dietary_restrictions", [])
            medical_conditions = profile.get("medical_conditions", [])
            
            # Create system prompt
            system_prompt = f"""
You are a professional nutritionist who specializes in creating personalized diet plans.
Your task is to generate weekly nutritional requirements for a person based on their profile.
Generate daily nutritional values for each day of the week and a weekly average.
The response should be structured as a JSON object with the following format:

{{
  "daily_requirements": {{
    "monday": {{
      "calories": float,
      "protein": float,  // grams
      "carbohydrates": float,  // grams
      "fat": float,  // grams
      "fiber": float,  // grams
      "sugar": float,  // grams (optional)
      "sodium": float,  // milligrams (optional)
      "vitamins": {{  // optional
        "vitamin_a": float,
        "vitamin_c": float,
        ...
      }}
    }},
    "tuesday": {{ ... }},
    ...
    "sunday": {{ ... }}
  }},
  "weekly_average": {{
    "calories": float,
    "protein": float,
    "carbohydrates": float,
    "fat": float,
    "fiber": float,
    "sugar": float,  // optional
    "sodium": float,  // optional
    "vitamins": {{ ... }}  // optional
  }}
}}

Consider the individual's specific needs and provide appropriate nutritional values.
Only respond with the JSON object, no additional text.
            """
            
            # Create user prompt with profile information
            user_prompt = f"""
Generate weekly nutritional requirements for a person with the following profile:
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

Please provide daily nutritional values for each day of the week (Monday through Sunday) and a weekly average.
            """
            
            # Call LLM API to generate diet requirements
            llm_response = await self.llm_client.generate_response(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.3  # Lower temperature for more consistent results
            )
            
            if not llm_response:
                return DietRequirement(
                    user_id=user_id,
                    created_at=datetime.utcnow(),
                    status=DietRequirementStatus.FAILED,
                    error_message="Failed to generate response from LLM"
                )
            
            # Parse the JSON response
            try:
                diet_data = json.loads(llm_response)
                
                # Convert the data to Pydantic models
                daily_requirements = {}
                for day, values in diet_data["daily_requirements"].items():
                    daily_requirements[day] = NutritionalValue(**values)
                
                weekly_average = NutritionalValue(**diet_data["weekly_average"])
                
                # Create and return the diet requirement object
                return DietRequirement(
                    user_id=user_id,
                    created_at=datetime.utcnow(),
                    status=DietRequirementStatus.COMPLETED,
                    daily_requirements=daily_requirements,
                    weekly_average=weekly_average,
                    llm_response=llm_response
                )
            except json.JSONDecodeError as e:
                return DietRequirement(
                    user_id=user_id,
                    created_at=datetime.utcnow(),
                    status=DietRequirementStatus.FAILED,
                    error_message=f"Failed to parse LLM response as JSON: {str(e)}",
                    llm_response=llm_response
                )
            except Exception as e:
                return DietRequirement(
                    user_id=user_id,
                    created_at=datetime.utcnow(),
                    status=DietRequirementStatus.FAILED,
                    error_message=f"Error processing LLM response: {str(e)}",
                    llm_response=llm_response
                )
                
        except Exception as e:
            return DietRequirement(
                user_id=user_id,
                created_at=datetime.utcnow(),
                status=DietRequirementStatus.FAILED,
                error_message=f"Error generating diet requirements: {str(e)}"
            )
    
    async def save_diet_requirements(self, diet_requirement: DietRequirement):
        """
        Save diet requirements to database
        """
        diet_plan_collection = await get_diet_plan_collection()
        
        # Convert Pydantic model to dict
        diet_dict = diet_requirement.dict()
        
        # Insert into database
        result = await diet_plan_collection.insert_one(diet_dict)
        
        # Return the ID of the inserted document
        return str(result.inserted_id)
    
    async def get_diet_requirement_by_id(self, requirement_id: str):
        """
        Get diet requirement by ID
        """
        diet_plan_collection = await get_diet_plan_collection()            
        diet_requirement = await diet_plan_collection.find_one({"_id": ObjectId(requirement_id)})
        if diet_requirement:
            diet_requirement["id"] = str(diet_requirement.pop("_id"))
            return diet_requirement
        
        return None
    
    async def get_latest_diet_requirement_for_user(self, user_id: str):
        """
        Get the latest diet requirement for a user
        """
        diet_plan_collection = await get_diet_plan_collection()
        diet_requirements = await diet_plan_collection.find(
            {"user_id": user_id}
        ).sort("created_at", -1).limit(1).to_list(length=1)
        
        if diet_requirements:
            diet_requirement = diet_requirements[0]
            diet_requirement["id"] = str(diet_requirement.pop("_id"))
            return diet_requirement
        
        return None
        
    # Keep backward compatibility with older code
    async def generate_diet_requirements(self, user_id: str) -> DietRequirement:
        """
        This method is kept for backward compatibility.
        In the new architecture, user profiles should be provided by the orchestrator.
        """
        return DietRequirement(
            user_id=user_id,
            created_at=datetime.utcnow(),
            status=DietRequirementStatus.FAILED,
            error_message="Direct database access not allowed. Please use the orchestrator service."
        )