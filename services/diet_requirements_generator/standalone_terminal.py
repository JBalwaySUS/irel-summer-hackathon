import asyncio
import sys
import os
import json
from datetime import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from services.shared.llm_client import LLMClient
from .models import DietRequirement, DietRequirementStatus, NutritionalValue

class StandaloneDietRequirementsTerminal:
    def __init__(self):
        self.llm_client = LLMClient()
    
    async def collect_user_profile(self):
        """Collect user profile information directly from the terminal"""
        print("\n===== USER PROFILE INFORMATION =====")
        
        # Collect basic information
        try:
            age = int(input("Age: "))
            gender = input("Gender (male/female/other): ").lower()
            height = float(input("Height (cm): "))
            weight = float(input("Weight (kg): "))
            
            # Diet type
            print("\nDiet Type Options:")
            print("1. Omnivore")
            print("2. Vegetarian")
            print("3. Vegan")
            print("4. Pescatarian")
            print("5. Keto")
            print("6. Paleo")
            print("7. Mediterranean")
            diet_choice = input("Select diet type (1-7): ")
            diet_types = ["omnivore", "vegetarian", "vegan", "pescatarian", "keto", "paleo", "mediterranean"]
            diet_type = diet_types[int(diet_choice) - 1] if diet_choice.isdigit() and 1 <= int(diet_choice) <= 7 else "omnivore"
            
            # Activity level
            print("\nActivity Level Options:")
            print("1. Sedentary (little or no exercise)")
            print("2. Lightly active (light exercise/sports 1-3 days/week)")
            print("3. Moderately active (moderate exercise/sports 3-5 days/week)")
            print("4. Very active (hard exercise/sports 6-7 days a week)")
            print("5. Extra active (very hard exercise & physical job or training twice a day)")
            activity_choice = input("Select activity level (1-5): ")
            activity_levels = ["sedentary", "lightly_active", "moderately_active", "very_active", "extra_active"]
            activity_level = activity_levels[int(activity_choice) - 1] if activity_choice.isdigit() and 1 <= int(activity_choice) <= 5 else "moderately_active"
            
            # Health goal
            print("\nHealth Goal Options:")
            print("1. Weight loss")
            print("2. Weight maintenance")
            print("3. Weight gain")
            print("4. Muscle building")
            print("5. General health improvement")
            goal_choice = input("Select health goal (1-5): ")
            health_goals = ["weight_loss", "weight_maintenance", "weight_gain", "muscle_building", "general_health"]
            health_goal = health_goals[int(goal_choice) - 1] if goal_choice.isdigit() and 1 <= int(goal_choice) <= 5 else "general_health"
            
            # Allergies
            allergies_input = input("\nEnter allergies (comma-separated, or press Enter for none): ")
            allergies = [allergy.strip() for allergy in allergies_input.split(",")] if allergies_input.strip() else []
            
            # Dietary restrictions
            restrictions_input = input("\nEnter dietary restrictions (comma-separated, or press Enter for none): ")
            dietary_restrictions = [restriction.strip() for restriction in restrictions_input.split(",")] if restrictions_input.strip() else []
            
            # Medical conditions
            conditions_input = input("\nEnter medical conditions (comma-separated, or press Enter for none): ")
            medical_conditions = [condition.strip() for condition in conditions_input.split(",")] if conditions_input.strip() else []
            
            # Create profile dictionary
            return {
                "age": age,
                "gender": gender,
                "height": height,
                "weight": weight,
                "diet_type": diet_type,
                "activity_level": activity_level,
                "health_goal": health_goal,
                "allergies": allergies,
                "dietary_restrictions": dietary_restrictions,
                "medical_conditions": medical_conditions
            }
        except ValueError:
            print("Error: Please enter valid numeric values for age, height, and weight.")
            return None
    
    async def generate_diet_requirements(self, user_profile):
        """Generate diet requirements based on user profile"""
        print("\n===== GENERATING DIET REQUIREMENTS =====")
        print("Generating personalized diet requirements based on your profile...")
        
        # Create system prompt
        system_prompt = """
You are a professional nutritionist who specializes in creating personalized diet plans.
Your task is to generate weekly nutritional requirements for a person based on their profile.
Generate daily nutritional values for each day of the week and a weekly average.
The response should be structured as a JSON object with the following format:

{
  "daily_requirements": {
    "monday": {
      "calories": float,
      "protein": float,  // grams
      "carbohydrates": float,  // grams
      "fat": float,  // grams
      "fiber": float,  // grams
      "sugar": float,  // grams (optional)
      "sodium": float,  // milligrams (optional)
      "vitamins": {  // optional
        "vitamin_a": float,
        "vitamin_c": float,
        ...
      }
    },
    "tuesday": { ... },
    ...
    "sunday": { ... }
  },
  "weekly_average": {
    "calories": float,
    "protein": float,
    "carbohydrates": float,
    "fat": float,
    "fiber": float,
    "sugar": float,  // optional
    "sodium": float,  // optional
    "vitamins": { ... }  // optional
  }
}

Consider the individual's specific needs and provide appropriate nutritional values.
Only respond with the JSON object, no additional text.
        """
        
        # Create user prompt
        user_prompt = f"""
Generate weekly nutritional requirements for a person with the following profile:
- Age: {user_profile['age']}
- Gender: {user_profile['gender']}
- Height: {user_profile['height']} cm
- Weight: {user_profile['weight']} kg
- Diet type: {user_profile['diet_type']}
- Activity level: {user_profile['activity_level']}
- Health goal: {user_profile['health_goal']}
- Allergies: {', '.join(user_profile['allergies']) if user_profile['allergies'] else 'None'}
- Dietary restrictions: {', '.join(user_profile['dietary_restrictions']) if user_profile['dietary_restrictions'] else 'None'}
- Medical conditions: {', '.join(user_profile['medical_conditions']) if user_profile['medical_conditions'] else 'None'}

Please provide daily nutritional values for each day of the week (Monday through Sunday) and a weekly average.
        """
        
        # Call LLM API to generate diet requirements
        try:
            llm_response = await self.llm_client.generate_response(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.3
            )
            
            if not llm_response:
                print("Error: Failed to generate response from LLM")
                return None
            
            # Parse the JSON response
            diet_data = json.loads(llm_response)
            
            # Add metadata
            result = {
                "daily_requirements": diet_data["daily_requirements"],
                "weekly_average": diet_data["weekly_average"],
                "user_profile": user_profile,
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
    
    def save_diet_requirements_to_file(self, diet_requirements, filename=None):
        """Save diet requirements to a JSON file"""
        if filename is None:
            filename = f"diet_requirements_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # Ensure the filename has .json extension
        if not filename.endswith('.json'):
            filename += '.json'
        
        try:
            with open(filename, 'w') as file:
                json.dump(diet_requirements, file, indent=2)
            print(f"\nDiet requirements saved to {filename}")
            return True
        except Exception as e:
            print(f"Error saving file: {str(e)}")
            return False
    
    def display_diet_requirements(self, diet_requirements):
        """Display diet requirements in a readable format"""
        print("\n===== DIET REQUIREMENTS =====")
        
        # Display daily requirements
        print("\nDaily Nutritional Requirements:")
        
        for day, values in diet_requirements["daily_requirements"].items():
            print(f"\n{day.capitalize()}:")
            print(f"  Calories: {values['calories']:.1f} kcal")
            print(f"  Protein: {values['protein']:.1f} g")
            print(f"  Carbohydrates: {values['carbohydrates']:.1f} g")
            print(f"  Fat: {values['fat']:.1f} g")
            print(f"  Fiber: {values['fiber']:.1f} g")
            
            if "sugar" in values:
                print(f"  Sugar: {values['sugar']:.1f} g")
            
            if "sodium" in values:
                print(f"  Sodium: {values['sodium']:.1f} mg")
            
            if "vitamins" in values and values["vitamins"]:
                print("  Vitamins:")
                for vitamin, amount in values["vitamins"].items():
                    print(f"    {vitamin.capitalize()}: {amount}")
        
        # Display weekly average
        print("\nWeekly Average:")
        weekly = diet_requirements["weekly_average"]
        print(f"  Calories: {weekly['calories']:.1f} kcal")
        print(f"  Protein: {weekly['protein']:.1f} g")
        print(f"  Carbohydrates: {weekly['carbohydrates']:.1f} g")
        print(f"  Fat: {weekly['fat']:.1f} g")
        print(f"  Fiber: {weekly['fiber']:.1f} g")
        
        if "sugar" in weekly:
            print(f"  Sugar: {weekly['sugar']:.1f} g")
        
        if "sodium" in weekly:
            print(f"  Sodium: {weekly['sodium']:.1f} mg")
        
        if "vitamins" in weekly and weekly["vitamins"]:
            print("  Vitamins:")
            for vitamin, amount in weekly["vitamins"].items():
                print(f"    {vitamin.capitalize()}: {amount}")
    
    async def run(self):
        """Run the standalone diet requirements generator"""
        print("Welcome to the Standalone Diet Requirements Generator")
        
        # Collect user profile
        user_profile = await self.collect_user_profile()
        if not user_profile:
            print("Failed to collect user profile. Exiting...")
            return
        
        # Generate diet requirements
        diet_requirements = await self.generate_diet_requirements(user_profile)
        if not diet_requirements:
            print("Failed to generate diet requirements. Exiting...")
            return
        
        # Display diet requirements
        self.display_diet_requirements(diet_requirements)
        
        # Ask if user wants to save to file
        save_choice = input("\nDo you want to save the diet requirements to a file? (y/n): ")
        if save_choice.lower() == 'y':
            filename = input("Enter filename (press Enter for default): ")
            filename = filename if filename.strip() else None
            self.save_diet_requirements_to_file(diet_requirements, filename)
        
        print("\nThank you for using the Diet Requirements Generator!")

async def main():
    terminal = StandaloneDietRequirementsTerminal()
    await terminal.run()

if __name__ == "__main__":
    asyncio.run(main())
