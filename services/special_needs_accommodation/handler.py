import sys
import os
import json
from datetime import datetime
from typing import Dict, Any, Optional
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from services.shared.llm_client import LLMClient
from services.shared.database import get_feedback_collection, get_special_needs_collection
from bson import ObjectId
from .models import UserFeedback, FeedbackAnalysis, AnalysisStatus

class SpecialNeedsHandler:
    def __init__(self):
        self.llm_client = LLMClient()
    
    async def save_feedback(self, feedback: UserFeedback):
        """
        Save user feedback to database
        """
        feedback_collection = await get_feedback_collection()
        
        # Convert Pydantic model to dict
        feedback_dict = feedback.dict()
        
        # Insert into database
        result = await feedback_collection.insert_one(feedback_dict)
        
        # Return the ID of the inserted document
        return str(result.inserted_id)
    
    async def analyze_feedback(self, feedback_id: str, food_recommendation: Dict = None, user_profile: Dict = None) -> FeedbackAnalysis:
        """
        Analyze user feedback to identify potential dietary restrictions or health concerns
        """
        try:
            # Get the feedback
            feedback_collection = await get_feedback_collection()
            feedback = await feedback_collection.find_one({"_id": ObjectId(feedback_id)})
            
            if not feedback:
                return FeedbackAnalysis(
                    feedback_id=feedback_id,
                    created_at=datetime.utcnow(),
                    status=AnalysisStatus.FAILED,
                    error_message="Feedback not found"
                )
            
            # Skip analysis for positive feedback
            if feedback["feedback_type"] == "positive":
                return FeedbackAnalysis(
                    feedback_id=feedback_id,
                    created_at=datetime.utcnow(),
                    status=AnalysisStatus.COMPLETED,
                    identified_concerns=[],
                    suggested_restrictions=[],
                    suggested_alternatives={},
                    recommendation="No concerns identified as feedback was positive."
                )
            
            # If food_recommendation wasn't passed, we'll use a placeholder
            if not food_recommendation:
                food_recommendation = {
                    "meal_plans": {}
                }
            
            # If user_profile wasn't passed, we'll use a placeholder
            if not user_profile:
                user_profile = {}
            
            # Create system prompt
            system_prompt = """
You are a professional nutritionist and dietician who specializes in identifying potential dietary restrictions, food allergies, and intolerances based on user feedback about meal plans.
Your task is to analyze negative feedback about a food recommendation and identify potential concerns, suggest dietary restrictions, and recommend alternatives.
Consider common food allergies, intolerances, and sensitivities such as gluten, lactose, nuts, seafood, etc.
The response should be structured as a JSON object with the following format:

{
  "identified_concerns": [
    "string", // e.g., "Bloating after consuming dairy products"
    ...
  ],
  "suggested_restrictions": [
    "string", // e.g., "Avoid dairy products"
    ...
  ],
  "suggested_alternatives": {
    "food_item": ["alternative1", "alternative2", ...], // e.g., "milk": ["almond milk", "soy milk", "oat milk"]
    ...
  },
  "recommendation": "string" // A brief summary of your analysis and recommendations
}

Be specific and practical in your analysis. Avoid making extreme recommendations unless clearly warranted.
Only respond with the JSON object, no additional text.
"""
            
            # Create user prompt with feedback and meal information
            user_prompt = f"""
User Feedback: "{feedback['feedback_text']}"

The feedback is about the following food recommendation:
"""
            
            # Add some meal plan details to the prompt if available
            if "meal_plans" in food_recommendation and food_recommendation["meal_plans"]:
                days = list(food_recommendation["meal_plans"].keys())
                if days:
                    first_day = days[0]  # Just include the first day to keep the prompt shorter
                    
                    user_prompt += f"Sample meals from {first_day.capitalize()} in the meal plan:\n"
                    
                    for meal in food_recommendation["meal_plans"][first_day].get("meals", []):
                        user_prompt += f"\n{meal['meal_type'].upper()}:\n"
                        for item in meal.get("food_items", []):
                            user_prompt += f"- {item['name']} ({item['quantity']})\n"
            
            # Add user profile information if available
            if user_profile:
                user_prompt += "\nUser profile information:\n"
                
                if "allergies" in user_profile and user_profile["allergies"]:
                    user_prompt += f"- Known allergies: {', '.join(user_profile['allergies'])}\n"
                
                if "dietary_restrictions" in user_profile and user_profile["dietary_restrictions"]:
                    user_prompt += f"- Known dietary restrictions: {', '.join(user_profile['dietary_restrictions'])}\n"
                
                if "medical_conditions" in user_profile and user_profile["medical_conditions"]:
                    user_prompt += f"- Medical conditions: {', '.join(user_profile['medical_conditions'])}\n"
            
            # Call LLM API to analyze feedback
            llm_response = await self.llm_client.generate_response(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.3  # Lower temperature for more consistent results
            )
            
            if not llm_response:
                return FeedbackAnalysis(
                    feedback_id=feedback_id,
                    created_at=datetime.utcnow(),
                    status=AnalysisStatus.FAILED,
                    error_message="Failed to generate response from LLM"
                )
            
            # Parse the JSON response
            try:
                # Clean the LLM response to remove Markdown code block formatting
                cleaned_response = llm_response
                
                # Remove opening code block markers (```json, ```, etc.)
                if "```" in cleaned_response:
                    # Find the first occurrence of an actual JSON character after the opening ```
                    start_index = cleaned_response.find("{")
                    if start_index != -1:
                        cleaned_response = cleaned_response[start_index:]
                
                # Remove closing code block markers (```)
                if "```" in cleaned_response:
                    end_index = cleaned_response.rfind("```")
                    if end_index != -1:
                        cleaned_response = cleaned_response[:end_index].strip()
                
                # Parse the cleaned JSON
                analysis_data = json.loads(cleaned_response)
                
                # Create and return the feedback analysis object
                return FeedbackAnalysis(
                    feedback_id=feedback_id,
                    created_at=datetime.utcnow(),
                    status=AnalysisStatus.COMPLETED,
                    identified_concerns=analysis_data.get("identified_concerns", []),
                    suggested_restrictions=analysis_data.get("suggested_restrictions", []),
                    suggested_alternatives=analysis_data.get("suggested_alternatives", {}),
                    recommendation=analysis_data.get("recommendation", ""),
                    llm_response=llm_response
                )
            except json.JSONDecodeError as e:
                return FeedbackAnalysis(
                    feedback_id=feedback_id,
                    created_at=datetime.utcnow(),
                    status=AnalysisStatus.FAILED,
                    error_message=f"Failed to parse LLM response as JSON: {str(e)}",
                    llm_response=llm_response
                )
            except Exception as e:
                return FeedbackAnalysis(
                    feedback_id=feedback_id,
                    created_at=datetime.utcnow(),
                    status=AnalysisStatus.FAILED,
                    error_message=f"Error processing LLM response: {str(e)}",
                    llm_response=llm_response
                )
                
        except Exception as e:
            return FeedbackAnalysis(
                feedback_id=feedback_id,
                created_at=datetime.utcnow(),
                status=AnalysisStatus.FAILED,
                error_message=f"Error analyzing feedback: {str(e)}"
            )
    
    async def save_analysis(self, analysis: FeedbackAnalysis):
        """
        Save feedback analysis to database
        """
        feedback_collection = await get_feedback_collection()
        
        # Convert Pydantic model to dict
        analysis_dict = analysis.dict()
        
        # Insert into database
        result = await feedback_collection.insert_one(analysis_dict)
        
        # Update the feedback document with the analysis ID
        await feedback_collection.update_one(
            {"_id": ObjectId(analysis.feedback_id)},
            {"$set": {"analysis_id": str(result.inserted_id)}}
        )
        
        # Return the ID of the inserted document
        return str(result.inserted_id)
    
    async def get_feedback_by_id(self, feedback_id: str):
        """
        Get feedback by ID
        """
        feedback_collection = await get_feedback_collection()
        feedback = await feedback_collection.find_one({"_id": ObjectId(feedback_id)})
        
        if feedback:
            feedback["id"] = str(feedback.pop("_id"))
            
            # If the feedback has an associated analysis, get it
            if "analysis_id" in feedback:
                analysis = await feedback_collection.find_one({"_id": ObjectId(feedback["analysis_id"])})
                if analysis:
                    analysis["id"] = str(analysis.pop("_id"))
                    feedback["analysis"] = analysis
            
            return feedback
        
        return None
    
    async def get_analysis_by_id(self, analysis_id: str):
        """
        Get feedback analysis by ID
        """
        feedback_collection = await get_feedback_collection()
        analysis = await feedback_collection.find_one({"_id": ObjectId(analysis_id)})
        
        if analysis:
            analysis["id"] = str(analysis.pop("_id"))
            return analysis
        
        return None
    
    async def get_user_feedbacks(self, user_id: str):
        """
        Get all feedbacks for a user
        """
        feedback_collection = await get_feedback_collection()
        feedbacks = await feedback_collection.find(
            {"user_id": user_id}
        ).sort("created_at", -1).to_list(length=10)
        
        if feedbacks:
            for feedback in feedbacks:
                feedback["id"] = str(feedback.pop("_id"))
                
                # If the feedback has an associated analysis, get it
                if "analysis_id" in feedback:
                    analysis = await feedback_collection.find_one({"_id": ObjectId(feedback["analysis_id"])})
                    if analysis:
                        analysis["id"] = str(analysis.pop("_id"))
                        feedback["analysis"] = analysis
            
            return feedbacks
        
        return []
    
    async def generate_plan_from_data(self, user_profile: Dict[str, Any], food_recommendation: Dict[str, Any], user_id: Optional[str] = None):
        """
        Generate special needs accommodation plan based on user profile and food recommendations provided by the orchestrator
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
                
            if not food_recommendation:
                return {
                    "user_id": user_id,
                    "created_at": datetime.utcnow(),
                    "status": "FAILED",
                    "error_message": "Food recommendation data not provided"
                }
            
            # Extract relevant profile data
            medical_conditions = user_profile.get("medical_conditions", [])
            allergies = user_profile.get("allergies", [])
            dietary_restrictions = user_profile.get("dietary_restrictions", [])
            
            # Only proceed with special needs accommodation if necessary
            if not medical_conditions and not allergies and not dietary_restrictions:
                return {
                    "user_id": user_id,
                    "created_at": datetime.utcnow(),
                    "status": "COMPLETED",
                    "message": "No special needs accommodation required",
                    "weekly_plan": food_recommendation.get("weekly_plan", {}),
                    "accommodations_made": []
                }
            
            # Create system prompt
            system_prompt = """
You are a dietitian who specializes in accommodating special dietary needs and medical conditions.
Your task is to review a meal plan and make necessary adjustments to accommodate allergies, 
dietary restrictions, and medical conditions.

Provide adjustments for each meal in the plan that needs to be modified.
The response should be structured as a JSON object.

Only respond with the JSON object, no additional text.
            """
            
            # Create user prompt with profile and food recommendation information
            user_prompt = f"""
Review and adjust the following meal plan for a person with these special needs:
- Medical conditions: {', '.join(medical_conditions) if medical_conditions else 'None'}
- Allergies: {', '.join(allergies) if allergies else 'None'}
- Dietary restrictions: {', '.join(dietary_restrictions) if dietary_restrictions else 'None'}

The current meal plan is:
{json.dumps(food_recommendation.get("weekly_plan", {}), indent=2)}

Please provide a modified meal plan that accommodates these special needs.
For each meal that needs to be adjusted, provide:
1. The original meal
2. The adjusted meal with substitutions
3. A brief explanation of the changes made
"""
            
            # Call LLM API to generate special needs accommodation
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
                # Clean the LLM response to remove Markdown code block formatting
                cleaned_response = llm_response
                
                # Remove opening code block markers (```json, ```, etc.)
                if "```" in cleaned_response:
                    # Find the first occurrence of an actual JSON character after the opening ```
                    start_index = cleaned_response.find("{")
                    if start_index != -1:
                        cleaned_response = cleaned_response[start_index:]
                
                # Remove closing code block markers (```)
                if "```" in cleaned_response:
                    end_index = cleaned_response.rfind("```")
                    if end_index != -1:
                        cleaned_response = cleaned_response[:end_index].strip()
                
                # Parse the cleaned JSON 
                special_needs_data = json.loads(cleaned_response)
                
                # Create and return the special needs plan object
                return {
                    "user_id": user_id,
                    "created_at": datetime.utcnow(),
                    "status": "COMPLETED",
                    "special_needs": {
                        "medical_conditions": medical_conditions,
                        "allergies": allergies,
                        "dietary_restrictions": dietary_restrictions
                    },
                    "original_plan": food_recommendation.get("weekly_plan", {}),
                    "adjusted_plan": special_needs_data,
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
                "error_message": f"Error generating special needs accommodation: {str(e)}"
            }
    
    async def save_plan(self, plan):
        """
        Save special needs plan to database
        """
        collection = await get_special_needs_collection()
        
        # Insert into database
        result = await collection.insert_one(plan)
        
        # Return the ID of the inserted document
        return str(result.inserted_id)
    
    async def get_plan_by_id(self, plan_id: str):
        """
        Get special needs plan by ID
        """
        collection = await get_special_needs_collection()
        plan = await collection.find_one({"_id": ObjectId(plan_id)})
        
        if plan:
            plan["id"] = str(plan.pop("_id"))
            return plan
        
        return None
    
    async def get_latest_plan_for_user(self, user_id: str):
        """
        Get the latest special needs plan for a user
        """
        collection = await get_special_needs_collection()
        plans = await collection.find(
            {"user_id": user_id}
        ).sort("created_at", -1).limit(1).to_list(length=1)
        
        if plans:
            plan = plans[0]
            plan["id"] = str(plan.pop("_id"))
            return plan
        
        return None