import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from services.shared.database import Database, get_user_collection
from .auth import get_password_hash, verify_password, create_access_token
from .models import DietType, ActivityLevel, HealthGoal
from bson import ObjectId
from datetime import datetime

class UserManagementTerminal:
    def __init__(self):
        self.current_user = None
        self.token = None
    
    async def init_db(self):
        await Database.connect_db()
    
    async def register(self):
        print("\n===== REGISTER =====")
        email = input("Email: ")
        name = input("Name: ")
        password = input("Password: ")
        
        # Check if user exists
        user_collection = await get_user_collection()
        existing_user = await user_collection.find_one({"email": email})
        
        if existing_user:
            print("Error: Email already registered")
            return
        
        # Create user
        hashed_password = get_password_hash(password)
        now = datetime.utcnow()
        
        user_dict = {
            "email": email,
            "name": name,
            "password": hashed_password,
            "created_at": now,
            "updated_at": now
        }
        
        result = await user_collection.insert_one(user_dict)
        print(f"Successfully registered user: {name}")
    
    async def login(self):
        print("\n===== LOGIN =====")
        email = input("Email: ")
        password = input("Password: ")
        
        user_collection = await get_user_collection()
        user = await user_collection.find_one({"email": email})
        
        if not user or not verify_password(password, user["password"]):
            print("Error: Invalid email or password")
            return
        
        self.token = create_access_token(data={"sub": str(user["_id"])})
        self.current_user = user
        self.current_user["id"] = str(self.current_user.pop("_id"))
        
        print(f"Successfully logged in as: {user['name']}")
    
    async def create_profile(self):
        if not self.current_user:
            print("Error: You must be logged in")
            return
        
        print("\n===== CREATE PROFILE =====")
        try:
            age = int(input("Age: "))
            gender = input("Gender: ")
            height = float(input("Height (cm): "))
            weight = float(input("Weight (kg): "))
            
            print("\nDiet Types:")
            for diet in DietType:
                print(f"- {diet.value}")
            diet_type = input("Diet Type: ")
            
            print("\nActivity Levels:")
            for level in ActivityLevel:
                print(f"- {level.value}")
            activity_level = input("Activity Level: ")
            
            print("\nHealth Goals:")
            for goal in HealthGoal:
                print(f"- {goal.value}")
            health_goal = input("Health Goal: ")
            
            allergies = input("Allergies (comma-separated): ").split(",")
            allergies = [a.strip() for a in allergies if a.strip()]
            
            dietary_restrictions = input("Dietary Restrictions (comma-separated): ").split(",")
            dietary_restrictions = [r.strip() for r in dietary_restrictions if r.strip()]
            
            medical_conditions = input("Medical Conditions (comma-separated): ").split(",")
            medical_conditions = [m.strip() for m in medical_conditions if m.strip()]
            
            # Validate inputs
            if not (0 < age < 120):
                print("Error: Invalid age")
                return
            
            if height <= 0 or weight <= 0:
                print("Error: Height and weight must be positive numbers")
                return
            
            if diet_type not in [d.value for d in DietType]:
                print("Error: Invalid diet type")
                return
            
            if activity_level not in [a.value for a in ActivityLevel]:
                print("Error: Invalid activity level")
                return
            
            if health_goal not in [h.value for h in HealthGoal]:
                print("Error: Invalid health goal")
                return
            
            # Create profile
            profile = {
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
            
            user_collection = await get_user_collection()
            await user_collection.update_one(
                {"_id": ObjectId(self.current_user["id"])},
                {"$set": {"profile": profile, "updated_at": datetime.utcnow()}}
            )
            
            print("Profile created successfully!")
            
        except ValueError:
            print("Error: Invalid input format")
    
    async def view_profile(self):
        if not self.current_user:
            print("Error: You must be logged in")
            return
        
        user_collection = await get_user_collection()
        user = await user_collection.find_one({"_id": ObjectId(self.current_user["id"])})
        
        if not user.get("profile"):
            print("Profile not found. Please create a profile first.")
            return
        
        profile = user["profile"]
        
        print("\n===== USER PROFILE =====")
        print(f"Name: {user['name']}")
        print(f"Email: {user['email']}")
        print(f"Age: {profile['age']}")
        print(f"Gender: {profile['gender']}")
        print(f"Height: {profile['height']} cm")
        print(f"Weight: {profile['weight']} kg")
        print(f"Diet Type: {profile['diet_type']}")
        print(f"Activity Level: {profile['activity_level']}")
        print(f"Health Goal: {profile['health_goal']}")
        print(f"Allergies: {', '.join(profile['allergies']) if profile['allergies'] else 'None'}")
        print(f"Dietary Restrictions: {', '.join(profile['dietary_restrictions']) if profile['dietary_restrictions'] else 'None'}")
        print(f"Medical Conditions: {', '.join(profile['medical_conditions']) if profile['medical_conditions'] else 'None'}")
    
    async def display_menu(self):
        while True:
            print("\n===== USER MANAGEMENT =====")
            print("1. Register")
            print("2. Login")
            print("3. Create Profile")
            print("4. View Profile")
            print("5. Exit")
            
            choice = input("Enter your choice (1-5): ")
            
            if choice == "1":
                await self.register()
            elif choice == "2":
                await self.login()
            elif choice == "3":
                await self.create_profile()
            elif choice == "4":
                await self.view_profile()
            elif choice == "5":
                print("Exiting...")
                await Database.close_db_connection()
                break
            else:
                print("Invalid choice. Please try again.")

async def main():
    terminal = UserManagementTerminal()
    await terminal.init_db()
    await terminal.display_menu()

if __name__ == "__main__":
    asyncio.run(main())