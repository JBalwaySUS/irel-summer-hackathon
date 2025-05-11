import asyncio
import sys
import os
import json
from datetime import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from services.shared.llm_client import LLMClient

class StandaloneFoodRecommendationTerminal:
    def __init__(self):
        self.llm_client = LLMClient()
    
    async def load_diet_requirements_from_file(self, file_path):
        """Load diet requirements from a JSON file"""
        try:
            with open(file_path, 'r') as file:
                diet_requirements = json.load(file)
            
            # Validate that it has the required fields
            if "daily_requirements" not in diet_requirements or "weekly_average" not in diet_requirements:
                print("Error: Invalid diet requirements file format")
                return None
            
            print("Diet requirements loaded successfully!")
            return diet_requirements
        except FileNotFoundError:
            print(f"Error: File not found: {file_path}")
            return None
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON format in file: {file_path}")
            return None
        except Exception as e:
            print(f"Error loading file: {str(e)}")
            return None
    
    def get_user_preferences(self):
        """Collect user preferences for meal planning"""
        print("\n===== MEAL PREFERENCES =====")
        
        # Food availability (optional)
        print("Do you want to specify available foods? (This is optional)")
        specify_foods = input("Enter 'y' for yes, any other key for no: ").lower() == 'y'
        
        food_availability = []
        if specify_foods:
            print("Enter available foods (one per line, empty line to finish):")
            while True:
                food = input("> ")
                if not food:
                    break
                food_availability.append(food)
        
        # Meal preferences (optional)
        print("\nDo you want to specify meal preferences? (This is optional)")
        specify_preferences = input("Enter 'y' for yes, any other key for no: ").lower() == 'y'
        
        meal_preferences = {}
        if specify_preferences:
            meal_types = ["breakfast", "lunch", "dinner", "snack"]
            for meal_type in meal_types:
                print(f"\nEnter {meal_type} preferences (comma-separated, empty to skip):")
                prefs = input("> ")
                if prefs:
                    meal_preferences[meal_type] = [p.strip() for p in prefs.split(",")]
        
        # Custom instructions for compensation
        print("\nEnter any custom instructions for meal compensation or adjustments:")
        print("For example: 'If I skip breakfast, increase lunch portion by 30%'")
        custom_instructions = input("> ")
        
        return {
            "food_availability": food_availability if food_availability else None,
            "meal_preferences": meal_preferences if meal_preferences else None,
            "custom_instructions": custom_instructions if custom_instructions else None
        }
    
    async def generate_food_recommendations(self, diet_requirements, user_preferences):
        """Generate food recommendations based on diet requirements and user preferences"""
        print("\n===== GENERATING FOOD RECOMMENDATIONS =====")
        print("Generating personalized meal plans based on your diet requirements...")
        
        # Extract user profile if available
        user_profile = diet_requirements.get("user_profile", {})
        if not user_profile:
            # Use basic profile data
            user_profile = {
                "diet_type": input("Diet type (e.g., omnivore, vegetarian, vegan): "),
                "allergies": input("Allergies (comma-separated, or press Enter for none): ").split(",") if input("Do you have allergies? (y/n): ").lower() == 'y' else [],
                "dietary_restrictions": input("Dietary restrictions (comma-separated, or press Enter for none): ").split(",") if input("Do you have dietary restrictions? (y/n): ").lower() == 'y' else []
            }
            # Clean up the lists by stripping whitespace
            user_profile["allergies"] = [a.strip() for a in user_profile["allergies"] if a.strip()]
            user_profile["dietary_restrictions"] = [r.strip() for r in user_profile["dietary_restrictions"] if r.strip()]
        
        # Create system prompt
        system_prompt = """
You are a professional nutritionist who specializes in creating personalized meal plans.
Your task is to generate a weekly meal plan based on nutritional requirements.
Generate meal plans for each day of the week with breakfast, lunch, dinner, and snacks.
The response should be structured as a JSON object.

Take into account any food availability constraints, meal preferences, and custom instructions for compensation.
For example, if the user says they might skip breakfast, suggest how they could compensate later in the day.

Only respond with the JSON object, no additional text.
        """
        
        # Prepare user prompt
        user_prompt = f"""
Generate a weekly meal plan based on the following nutritional requirements:

Weekly Average:
- Calories: {diet_requirements['weekly_average']['calories']:.1f} kcal
- Protein: {diet_requirements['weekly_average']['protein']:.1f} g
- Carbohydrates: {diet_requirements['weekly_average']['carbohydrates']:.1f} g
- Fat: {diet_requirements['weekly_average']['fat']:.1f} g
- Fiber: {diet_requirements['weekly_average']['fiber']:.1f} g
"""

        # Add diet type, allergies, and dietary restrictions if available
        if user_profile:
            user_prompt += f"\nDiet type: {user_profile.get('diet_type', 'Not specified')}\n"
            
            allergies = user_profile.get('allergies', [])
            if allergies:
                user_prompt += f"Allergies: {', '.join(allergies)}\n"
            
            dietary_restrictions = user_profile.get('dietary_restrictions', [])
            if dietary_restrictions:
                user_prompt += f"Dietary restrictions: {', '.join(dietary_restrictions)}\n"
        
        # Add food availability if specified
        if user_preferences.get('food_availability'):
            user_prompt += "\nAvailable foods (only use these):\n"
            for food in user_preferences['food_availability']:
                user_prompt += f"- {food}\n"
        
        # Add meal preferences if specified
        if user_preferences.get('meal_preferences'):
            user_prompt += "\nMeal preferences:\n"
            for meal_type, preferences in user_preferences['meal_preferences'].items():
                user_prompt += f"- {meal_type.capitalize()}: {', '.join(preferences)}\n"
        
        # Add custom instructions if specified
        if user_preferences.get('custom_instructions'):
            user_prompt += f"\nCustom instructions for meal adjustments and compensation:\n"
            user_prompt += f"{user_preferences['custom_instructions']}\n"
        
        # Call LLM API to generate food recommendations
        try:
            llm_response = await self.llm_client.generate_response(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.5
            )
            
            if not llm_response:
                print("Error: Failed to generate response from LLM")
                return None
            
            # Parse the JSON response
            food_recommendation_data = json.loads(llm_response)
            
            # Add metadata
            result = {
                "meal_plans": food_recommendation_data,
                "diet_requirements": {
                    "weekly_average": diet_requirements["weekly_average"]
                },
                "user_preferences": user_preferences,
                "created_at": datetime.utcnow().isoformat(),
                "status": "COMPLETED"
            }
            
            return result
            
        except json.JSONDecodeError as e:
            print(f"Error: Failed to parse LLM response as JSON: {str(e)}")
            return None
        except Exception as e:
            print(f"Error: {str(e)}")
            return None
    
    def save_food_recommendations_to_file(self, food_recommendations, filename=None):
        """Save food recommendations to a JSON file"""
        if filename is None:
            filename = f"food_recommendations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # Ensure the filename has .json extension
        if not filename.endswith('.json'):
            filename += '.json'
        
        try:
            with open(filename, 'w') as file:
                json.dump(food_recommendations, file, indent=2)
            print(f"\nFood recommendations saved to {filename}")
            return True
        except Exception as e:
            print(f"Error saving file: {str(e)}")
            return False
    
    def display_food_recommendations(self, food_recommendations):
        """Display food recommendations in a readable format"""
        print("\n===== FOOD RECOMMENDATIONS =====")
        
        meal_plans = food_recommendations.get("meal_plans", {})
        
        # Display meal plans for each day
        for day, plan in meal_plans.items():
            print(f"\n{day.upper()} MEAL PLAN:")
            
            # Display meals
            for meal_key in ["breakfast", "lunch", "dinner", "snacks"]:
                if meal_key in plan:
                    print(f"\n  {meal_key.upper()}:")
                    meal = plan[meal_key]
                    
                    # Check if meal is a string or a dict
                    if isinstance(meal, str):
                        print(f"    {meal}")
                    elif isinstance(meal, dict):
                        # Handle different formats
                        if "description" in meal:
                            print(f"    {meal['description']}")
                        if "items" in meal:
                            for item in meal["items"]:
                                print(f"    - {item}")
                        if "ingredients" in meal:
                            print("    Ingredients:")
                            for ingredient in meal["ingredients"]:
                                print(f"      - {ingredient}")
                        if "preparation" in meal:
                            print(f"    Preparation: {meal['preparation']}")
                    elif isinstance(meal, list):
                        for item in meal:
                            if isinstance(item, str):
                                print(f"    - {item}")
                            elif isinstance(item, dict) and "name" in item:
                                print(f"    - {item['name']}: {item.get('quantity', '')}")
    
    async def run(self):
        """Run the standalone food recommendation generator"""
        print("Welcome to the Standalone Food Recommendation Generator")
        
        # Ask for diet requirements file
        file_path = input("\nEnter the path to your diet requirements JSON file: ")
        diet_requirements = await self.load_diet_requirements_from_file(file_path)
        
        if not diet_requirements:
            print("Failed to load diet requirements. Exiting...")
            return
        
        # Get user preferences
        user_preferences = self.get_user_preferences()
        
        # Generate food recommendations
        food_recommendations = await self.generate_food_recommendations(diet_requirements, user_preferences)
        
        if not food_recommendations:
            print("Failed to generate food recommendations. Exiting...")
            return
        
        # Display food recommendations
        self.display_food_recommendations(food_recommendations)
        
        # Ask if user wants to save to file
        save_choice = input("\nDo you want to save the food recommendations to a file? (y/n): ")
        if save_choice.lower() == 'y':
            filename = input("Enter filename (press Enter for default): ")
            filename = filename if filename.strip() else None
            self.save_food_recommendations_to_file(food_recommendations, filename)
        
        print("\nThank you for using the Food Recommendation Generator!")

async def main():
    terminal = StandaloneFoodRecommendationTerminal()
    await terminal.run()

if __name__ == "__main__":
    asyncio.run(main())
