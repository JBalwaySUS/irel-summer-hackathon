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
    
    async def _create_diet_prompt(self, profile: Dict[str, Any]) -> tuple:
        """
        Create system and user prompts for the LLM based on user profile
        This is a private helper method used by other methods
        """
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
        "calories": float,  // REQUIRED - daily caloric intake
        "protein": float,   // REQUIRED - in grams
        "carbohydrates": float,  // REQUIRED - in grams
        "fat": float,       // REQUIRED - in grams
        "fiber": float,     // REQUIRED - in grams
        "sugar": float,     // optional - in grams
        "sodium": float,    // optional - in milligrams
        "vitamins": {{      // optional
            "vitamin_a": float,
            "vitamin_c": float,
            ...
        }}
        }},
        "tuesday": {{ ... }},
        "wednesday": {{ ... }},
        "thursday": {{ ... }},
        "friday": {{ ... }},
        "saturday": {{ ... }},
        "sunday": {{ ... }}
    }},
    "weekly_average": {{
        "calories": float,    // REQUIRED
        "protein": float,     // REQUIRED - in grams
        "carbohydrates": float,  // REQUIRED - in grams
        "fat": float,         // REQUIRED - in grams
        "fiber": float,       // REQUIRED - in grams
        "sugar": float,       // optional - in grams
        "sodium": float,      // optional - in milligrams
        "vitamins": {{ ... }} // optional
    }}
    }}

    IMPORTANT: Every daily entry and the weekly average MUST include ALL the REQUIRED fields (calories, protein, carbohydrates, fat, and fiber).
    Optional fields can be omitted if not relevant.
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
    Remember to include ALL required fields: calories, protein, carbohydrates, fat, and fiber for EACH day.
        """
        
        return system_prompt, user_prompt
    
    async def _process_llm_response(self, llm_response: str, user_id: str) -> DietRequirement:
        """
        Process the LLM response and convert it to a DietRequirement object
        This is a private helper method used by other methods
        """
        try:
             # Clean up the response if it contains markdown code blocks
            if llm_response.strip().startswith("```"):
                # Strip out the markdown code block syntax
                json_str = llm_response.strip()
                
                # Remove opening code block marker (```json or just ```)
                first_newline = json_str.find('\n')
                if first_newline != -1:
                    json_str = json_str[first_newline:].strip()
                
                # Remove closing code block marker if present
                if json_str.endswith("```"):
                    json_str = json_str[:-3].strip()
                    
                print(f"Cleaned LLM Response: {json_str}")  # Debugging line
                diet_data = json.loads(json_str)
            else:
                diet_data = json.loads(llm_response)
            
            print(f"Parsed LLM Response: {diet_data}")  # Debugging line
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
    
    async def generate_diet_requirements_from_profile(self, user_profile: Dict[str, Any], user_id: str = None) -> DietRequirement:
        """
        Generate diet requirements based on user profile data
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
            
            # Create prompts
            system_prompt, user_prompt = await self._create_diet_prompt(user_profile)
            
            # Call LLM API to generate diet requirements
            llm_response = await self.llm_client.generate_response(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.3  # Lower temperature for more consistent results
            )
            
            print(f"LLM Response: {llm_response}")  # Debugging line

            if not llm_response:
                return DietRequirement(
                    user_id=user_id,
                    created_at=datetime.utcnow(),
                    status=DietRequirementStatus.FAILED,
                    error_message="Failed to generate response from LLM"
                )
            
            # Process the LLM response
            return await self._process_llm_response(llm_response, user_id)
                
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
            diet_requirement["status_code"] = 200
            return diet_requirement
        
        return None
        