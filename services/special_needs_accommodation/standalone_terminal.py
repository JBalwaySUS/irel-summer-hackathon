import asyncio
import sys
import os
import json
from datetime import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from services.shared.llm_client import LLMClient

class StandaloneSpecialNeedsTerminal:
    def __init__(self):
        self.llm_client = LLMClient()
    
    async def load_food_recommendations_from_file(self, file_path):
        """Load food recommendations from a JSON file"""
        try:
            with open(file_path, 'r') as file:
                food_recommendations = json.load(file)
            
            # Validate that it has the required fields
            if "meal_plans" not in food_recommendations:
                print("Error: Invalid food recommendations file format")
                return None
            
            print("Food recommendations loaded successfully!")
            return food_recommendations
        except FileNotFoundError:
            print(f"Error: File not found: {file_path}")
            return None
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON format in file: {file_path}")
            return None
        except Exception as e:
            print(f"Error loading file: {str(e)}")
            return None
      def collect_special_needs_info(self):
        """Collect symptom information directly from the terminal"""
        print("\n===== SYMPTOM AND DIETARY ISSUE REPORTING =====")
        print("Please share any symptoms or discomfort you experience after eating certain foods.")
        print("The system will analyze your symptoms and suggest appropriate dietary adjustments.")
        
        # Collect reported symptoms
        print("\nDo you experience any symptoms or discomfort after eating?")
        has_symptoms = input("Enter 'y' for yes, any other key for no: ").lower() == 'y'
        
        reported_symptoms = []
        if has_symptoms:
            print("Enter symptoms (one per line, empty line to finish):")
            print("Examples: bloating after dairy, headache after wine, stomach pain after wheat products")
            while True:
                symptom = input("> ")
                if not symptom:
                    break
                reported_symptoms.append(symptom)
        
        # Collect any known allergies
        print("\nDo you have any confirmed allergies or intolerances?")
        has_allergies = input("Enter 'y' for yes, any other key for no: ").lower() == 'y'
        
        known_allergies = []
        if has_allergies:
            print("Enter allergies or intolerances (one per line, empty line to finish):")
            while True:
                allergy = input("> ")
                if not allergy:
                    break
                known_allergies.append(allergy)
        
        # Collect food preferences or aversions
        print("\nAre there any foods you prefer to avoid or dislike?")
        has_aversions = input("Enter 'y' for yes, any other key for no: ").lower() == 'y'
        
        food_aversions = []
        if has_aversions:
            print("Enter foods you prefer to avoid (one per line, empty line to finish):")
            while True:
                aversion = input("> ")
                if not aversion:
                    break
                food_aversions.append(aversion)
        
        # Additional information
        print("\nPlease provide any additional details about your diet or health history:")
        print("For example: family history of conditions, recent dietary changes, medication use")
        additional_info = input("> ")
        
        return {
            "reported_symptoms": reported_symptoms,
            "known_allergies": known_allergies,
            "food_aversions": food_aversions,
            "additional_info": additional_info if additional_info else None
        }
      async def generate_special_needs_plan(self, food_recommendations, symptom_info):
        """Generate special needs accommodation plan based on reported symptoms"""
        print("\n===== ANALYZING SYMPTOMS AND GENERATING DIETARY ACCOMMODATIONS =====")
        print("Analyzing your reported symptoms and adjusting meal plans accordingly...")
        
        # Check if any symptoms are specified
        if not symptom_info["reported_symptoms"] and not symptom_info["known_allergies"] and not symptom_info["food_aversions"]:
            print("No symptoms or dietary concerns reported. The original meal plan will be used.")
            return {
                "original_plan": food_recommendations["meal_plans"],
                "adjusted_plan": food_recommendations["meal_plans"],
                "symptom_info": symptom_info,
                "message": "No dietary accommodations required",
                "accommodations_made": [],
                "created_at": datetime.utcnow().isoformat(),
                "status": "COMPLETED"
            }
        
        # Create system prompt
        system_prompt = """
You are a registered dietitian with a specialization in identifying potential food sensitivities, allergies, and intolerances based on reported symptoms.

Your task is to:
1. Analyze the reported symptoms and identify potential food-related issues or medical conditions
2. Provide educational information about the potential medical conditions based on the symptoms
3. Make appropriate adjustments to the meal plan to accommodate these concerns
4. Explain what foods should be avoided and why, based on the symptoms

Format your response as a JSON object with these sections:
1. "analysis": Detailed analysis of symptoms and potential causes
2. "potential_conditions": List of potential medical conditions with brief descriptions
3. "dietary_recommendations": General dietary guidelines based on the analysis
4. "adjusted_plan": Modified meal plan with substitutions
5. "food_substitutions": List of specific foods to avoid and their alternatives

Be respectful and note that this is not a medical diagnosis but rather educated dietary guidance.
"""
        
        # Create user prompt
        user_prompt = f"""
Please analyze these reported symptoms and dietary concerns:
- Reported symptoms: {', '.join(symptom_info['reported_symptoms']) if symptom_info['reported_symptoms'] else 'None'}
- Known allergies/intolerances: {', '.join(symptom_info['known_allergies']) if symptom_info['known_allergies'] else 'None'}
- Foods preferred to avoid: {', '.join(symptom_info['food_aversions']) if symptom_info['food_aversions'] else 'None'}
{f"- Additional information: {symptom_info['additional_info']}" if symptom_info.get('additional_info') else ""}

The current meal plan is:
{json.dumps(food_recommendations['meal_plans'], indent=2)}

Please provide a comprehensive analysis of potential food sensitivities or medical conditions based on the symptoms,
educational information about these conditions, and a modified meal plan that accommodates these concerns.
"""
        
        # Call LLM API to generate special needs accommodation
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
            special_needs_data = json.loads(llm_response)
            
            # Create the result
            result = {
                "original_plan": food_recommendations["meal_plans"],
                "adjusted_plan": special_needs_data.get("adjusted_plan", {}),
                "symptom_analysis": special_needs_data.get("analysis", ""),
                "potential_conditions": special_needs_data.get("potential_conditions", []),
                "dietary_recommendations": special_needs_data.get("dietary_recommendations", []),
                "food_substitutions": special_needs_data.get("food_substitutions", {}),
                "symptom_info": symptom_info,
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
    
    def save_special_needs_plan_to_file(self, special_needs_plan, filename=None):
        """Save special needs plan to a JSON file"""
        if filename is None:
            filename = f"special_needs_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # Ensure the filename has .json extension
        if not filename.endswith('.json'):
            filename += '.json'
        
        try:
            with open(filename, 'w') as file:
                json.dump(special_needs_plan, file, indent=2)
            print(f"\nSpecial needs plan saved to {filename}")
            return True
        except Exception as e:
            print(f"Error saving file: {str(e)}")
            return False
    
    def display_special_needs_plan(self, special_needs_plan):
        """Display special needs plan in a readable format"""
        print("\n===== SPECIAL NEEDS ACCOMMODATION PLAN =====")
        
        # Check if any accommodations were needed
        if "message" in special_needs_plan and special_needs_plan["message"] == "No special needs accommodation required":
            print("\nNo special needs accommodation required. The original meal plan is suitable.")
            return
        
        print("\nAdjustments made to accommodate special needs:")
        
        adjusted_plan = special_needs_plan.get("adjusted_plan", {})
        
        # Display the adjusted meal plan
        for day, meals in adjusted_plan.items():
            print(f"\n{day.upper()}:")
            
            # Check different possible formats of the response
            if isinstance(meals, dict):
                # Format 1: {day: {meal_type: {original: ..., adjusted: ..., explanation: ...}}}
                for meal_type, meal_data in meals.items():
                    print(f"\n  {meal_type.upper()}:")
                    
                    if isinstance(meal_data, dict):
                        if "original" in meal_data and "adjusted" in meal_data:
                            # There was an adjustment
                            print(f"    Original: {meal_data.get('original', '')}")
                            print(f"    Adjusted: {meal_data.get('adjusted', '')}")
                            
                            if "explanation" in meal_data:
                                print(f"    Explanation: {meal_data['explanation']}")
                        else:
                            # Regular meal data
                            if "description" in meal_data:
                                print(f"    {meal_data['description']}")
                            elif "items" in meal_data:
                                for item in meal_data["items"]:
                                    print(f"    - {item}")
                    elif isinstance(meal_data, str):
                        print(f"    {meal_data}")
                    elif isinstance(meal_data, list):
                        for item in meal_data:
                            print(f"    - {item}")
            
            # Format 2: {day: {breakfast: ..., lunch: ..., dinner: ...}}
            elif "breakfast" in meals or "lunch" in meals or "dinner" in meals:
                for meal_type in ["breakfast", "lunch", "dinner", "snacks"]:
                    if meal_type in meals:
                        print(f"\n  {meal_type.upper()}:")
                        meal = meals[meal_type]
                        
                        if isinstance(meal, str):
                            print(f"    {meal}")
                        elif isinstance(meal, dict):
                            if "description" in meal:
                                print(f"    {meal['description']}")
                            elif "items" in meal:
                                for item in meal["items"]:
                                    print(f"    - {item}")
                        elif isinstance(meal, list):
                            for item in meal:
                                print(f"    - {item}")
    
    async def run(self):
        """Run the standalone special needs accommodation terminal"""
        print("Welcome to the Standalone Special Needs Accommodation Terminal")
        
        # Ask for food recommendations file
        file_path = input("\nEnter the path to your food recommendations JSON file: ")
        food_recommendations = await self.load_food_recommendations_from_file(file_path)
        
        if not food_recommendations:
            print("Failed to load food recommendations. Exiting...")
            return
        
        # Collect special needs information
        special_needs = self.collect_special_needs_info()
        
        # Generate special needs plan
        special_needs_plan = await self.generate_special_needs_plan(food_recommendations, special_needs)
        
        if not special_needs_plan:
            print("Failed to generate special needs plan. Exiting...")
            return
        
        # Display special needs plan
        self.display_special_needs_plan(special_needs_plan)
        
        # Ask if user wants to save to file
        save_choice = input("\nDo you want to save the special needs plan to a file? (y/n): ")
        if save_choice.lower() == 'y':
            filename = input("Enter filename (press Enter for default): ")
            filename = filename if filename.strip() else None
            self.save_special_needs_plan_to_file(special_needs_plan, filename)
        
        print("\nThank you for using the Special Needs Accommodation Terminal!")

async def main():
    terminal = StandaloneSpecialNeedsTerminal()
    await terminal.run()

if __name__ == "__main__":
    asyncio.run(main())
