import streamlit as st
import requests
import json
from datetime import datetime
import pandas as pd
import time
import os

# Service URLs - Read from environment variables, with local defaults
USER_MANAGEMENT_URL = os.getenv("USER_MANAGEMENT_URL", "http://user-management:8000/api/v1")
DIET_REQUIREMENTS_URL = os.getenv("DIET_REQUIREMENTS_URL", "http://diet-requirements:8001/api/v1")
FOOD_RECOMMENDATION_URL = os.getenv("FOOD_RECOMMENDATION_URL", "http://food-recommendation:8002/api/v1")
SPECIAL_NEEDS_URL = os.getenv("SPECIAL_NEEDS_URL", "http://special-needs:8003/api/v1")

# Initialize session state
if "user" not in st.session_state:
    st.session_state.user = None
if "token" not in st.session_state:
    st.session_state.token = None

# Page title
st.title("Virtual Dietician")

# Authentication functions
def login(email, password):
    try:
        response = requests.post(
            f"{USER_MANAGEMENT_URL}/token",
            data={"username": email, "password": password}
        )
        if response.status_code == 200:
            data = response.json()
            st.session_state.token = data["access_token"]
            get_user_profile()
            return True
        else:
            return False
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return False

def register(email, name, password):
    try:
        response = requests.post(
            f"{USER_MANAGEMENT_URL}/users/register",
            json={"email": email, "name": name, "password": password}
        )
        if response.status_code == 201:
            return True
        else:
            st.error(f"Error: {response.json()['detail']}")
            return False
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return False

def get_user_profile():
    if not st.session_state.token:
        return None
    
    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    
    try:
        response = requests.get(
            f"{USER_MANAGEMENT_URL}/users/me",
            headers=headers
        )
        if response.status_code == 200:
            st.session_state.user = response.json()
            return st.session_state.user
        else:
            st.error("Failed to get user profile")
            return None
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None

def create_profile(profile_data):
    if not st.session_state.token:
        return False
    
    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    
    try:
        response = requests.post(
            f"{USER_MANAGEMENT_URL}/users/profile",
            json=profile_data,
            headers=headers
        )
        if response.status_code == 200:
            st.session_state.user = response.json()
            return True
        else:
            st.error(f"Error: {response.json()['detail']}")
            return False
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return False

def update_profile(profile_data):
    if not st.session_state.token:
        return False
    
    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    
    try:
        response = requests.put(
            f"{USER_MANAGEMENT_URL}/users/profile",
            json=profile_data,
            headers=headers
        )
        if response.status_code == 200:
            st.session_state.user = response.json()
            return True
        else:
            st.error(f"Error: {response.json()['detail']}")
            return False
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return False

# Diet Requirements functions
def generate_diet_requirements():
    if not st.session_state.token:
        st.error("You must be logged in to generate diet requirements")
        return None
    
    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    
    try:
        with st.spinner("Generating diet requirements..."):
            # First, verify that the token is still valid by making a simple request
            verify_response = requests.get(
                f"{USER_MANAGEMENT_URL}/users/me",
                headers=headers
            )
            
            if verify_response.status_code != 200:
                # Token is invalid, need to re-login
                st.error("Your session has expired. Please log in again.")
                st.session_state.token = None
                st.session_state.user = None
                time.sleep(1)
                st.experimental_rerun()
                return None
            
            # Get user data to send to the service
            user_data = st.session_state.user
            
            # Call the diet requirements service directly
            response = requests.post(
                f"{DIET_REQUIREMENTS_URL}/diet-requirements",
                json={"user_data": user_data},
                headers=headers
            )
            
            if response.status_code == 201:
                return response.json()
            elif response.status_code == 401:
                st.error("Authentication failed. Please log in again.")
                st.session_state.token = None
                st.session_state.user = None
                time.sleep(1)
                st.experimental_rerun()
                return None
            else:
                error_detail = "Unknown error"
                try:
                    error_detail = response.json().get('detail', 'Unknown error')
                except:
                    pass
                st.error(f"Error: {error_detail}, Response code: {response.status_code}")
                return None
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None

def get_latest_diet_requirements():
    if not st.session_state.token:
        return None
    
    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    
    try:
        # Get user_id from the user object
        user_id = st.session_state.user["id"]
        
        # Call the diet requirements service directly
        response = requests.get(
            f"{DIET_REQUIREMENTS_URL}/diet-requirements/user/{user_id}/latest",
            headers=headers
        )
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception:
        return None

# Food Recommendation functions
def generate_food_recommendation(diet_requirement_id, food_availability=None, meal_preferences=None):
    if not st.session_state.token:
        return None
    
    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    user_id = st.session_state.user["id"]
    user_data = st.session_state.user
    
    diet_requirements = get_latest_diet_requirements()
    if not diet_requirements:
        st.error("Please generate diet requirements first")
        return None
    
    # Prepare request data
    request_data = {
        "user_data": user_data,
        "diet_requirement": diet_requirements,
        "food_availability": food_availability,
        "meal_preferences": meal_preferences
    }
    
    try:
        with st.spinner("Generating meal recommendations..."):
            # Call the food recommendation service directly
            response = requests.post(
                f"{FOOD_RECOMMENDATION_URL}/food-recommendation",
                json=request_data,
                headers=headers
            )
            if response.status_code == 201:  # Changed from 200 to 201
                return response.json()
            else:
                st.error(f"Error: {response.json().get('detail', 'Unknown error')}")
                return None
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None

def get_latest_food_recommendation():
    if not st.session_state.token:
        return None
    
    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    user_id = st.session_state.user["id"]
    
    try:
        # Call the food recommendation service directly
        response = requests.get(
            f"{FOOD_RECOMMENDATION_URL}/food-recommendation/user/{user_id}/latest",
            headers=headers
        )
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception:
        return None

# Feedback functions
def submit_feedback(food_recommendation_id, feedback_text, feedback_type):
    if not st.session_state.token or not st.session_state.user:
        return None
    
    user_data = st.session_state.user
    
    # Get the food recommendation to include in request
    food_recommendation = get_latest_food_recommendation()
    
    data = {
        "user_data": user_data,
        "food_recommendation_id": food_recommendation_id,
        "food_recommendation": food_recommendation,  # Include full recommendation data
        "feedback_text": feedback_text,
        "feedback_type": feedback_type
    }
    
    try:
        with st.spinner("Processing feedback..."):
            # Call the special needs service directly for feedback
            response = requests.post(
                f"{SPECIAL_NEEDS_URL}/api/v1/feedback",
                json=data
            )
            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"Error: {response.json().get('detail', 'Unknown error')}")
                return None
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None

def get_user_feedbacks():
    if not st.session_state.user:
        return None
    
    user_id = st.session_state.user["id"]
    
    try:
        # Call the special needs service directly for user feedbacks
        response = requests.get(
            f"{SPECIAL_NEEDS_URL}/feedback/user/{user_id}"
        )
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception:
        return None

# Sidebar navigation
def sidebar_navigation():
    st.sidebar.title("Navigation")
    
    if st.session_state.user:
        options = [
            "Profile",
            "Diet Requirements",
            "Meal Recommendations",
            "Feedback & Analysis"
        ]
        
        choice = st.sidebar.selectbox("Go to", options)
        
        if choice == "Profile":
            display_profile_page()
        elif choice == "Diet Requirements":
            display_diet_requirements_page()
        elif choice == "Meal Recommendations":
            display_meal_recommendations_page()
        elif choice == "Feedback & Analysis":
            display_feedback_page()
        
        if st.sidebar.button("Logout"):
            st.session_state.user = None
            st.session_state.token = None
            st.experimental_rerun()
    else:
        display_auth_page()

# Page displays
def display_auth_page():
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        st.header("Login")
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Login"):
            if login(email, password):
                st.success("Login successful!")
                time.sleep(1)
                st.experimental_rerun()
            else:
                st.error("Invalid email or password")
    
    with tab2:
        st.header("Register")
        name = st.text_input("Name", key="register_name")
        email = st.text_input("Email", key="register_email")
        password = st.text_input("Password", type="password", key="register_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="register_confirm_password")
        
        if st.button("Register"):
            if password != confirm_password:
                st.error("Passwords do not match")
            elif register(email, name, password):
                st.success("Registration successful! Please login.")
                time.sleep(1)
                st.experimental_rerun()

def display_profile_page():
    st.header("User Profile")
    
    user = st.session_state.user
    
    if not user.get("profile"):
        st.subheader("Create Profile")
        
        # Form for creating profile
        with st.form("profile_form"):
            age = st.number_input("Age", min_value=1, max_value=120)
            gender = st.selectbox("Gender", ["Male", "Female", "Other"])
            height = st.number_input("Height (cm)", min_value=1.0)
            weight = st.number_input("Weight (kg)", min_value=1.0)
            
            diet_type = st.selectbox(
                "Diet Type",
                ["non-vegetarian", "vegetarian", "vegan"]
            )
            
            activity_level = st.selectbox(
                "Activity Level",
                ["sedentary", "light", "moderate", "active", "very-active"]
            )
            
            health_goal = st.selectbox(
                "Health Goal",
                ["weight-loss", "weight-gain", "maintenance", "muscle-gain", "general-health"]
            )
            
            allergies = st.text_input("Allergies (comma-separated)")
            dietary_restrictions = st.text_input("Dietary Restrictions (comma-separated)")
            medical_conditions = st.text_input("Medical Conditions (comma-separated)")
            
            submit_button = st.form_submit_button("Create Profile")
            
            if submit_button:
                # Process form data
                profile_data = {
                    "age": age,
                    "gender": gender,
                    "height": height,
                    "weight": weight,
                    "diet_type": diet_type,
                    "activity_level": activity_level,
                    "health_goal": health_goal,
                    "allergies": [item.strip() for item in allergies.split(",") if item.strip()],
                    "dietary_restrictions": [item.strip() for item in dietary_restrictions.split(",") if item.strip()],
                    "medical_conditions": [item.strip() for item in medical_conditions.split(",") if item.strip()]
                }
                
                if create_profile(profile_data):
                    st.success("Profile created successfully!")
                    time.sleep(1)
                    st.experimental_rerun()
    else:
        # Display current profile
        profile = user["profile"]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Personal Information")
            st.write(f"**Name:** {user['name']}")
            st.write(f"**Email:** {user['email']}")
            st.write(f"**Age:** {profile['age']}")
            st.write(f"**Gender:** {profile['gender']}")
        
        with col2:
            st.subheader("Health Information")
            st.write(f"**Height:** {profile['height']} cm")
            st.write(f"**Weight:** {profile['weight']} kg")
            st.write(f"**Diet Type:** {profile['diet_type']}")
            st.write(f"**Activity Level:** {profile['activity_level']}")
            st.write(f"**Health Goal:** {profile['health_goal']}")
        
        st.subheader("Additional Information")
        
        if profile.get("allergies"):
            st.write(f"**Allergies:** {', '.join(profile['allergies'])}")
        else:
            st.write("**Allergies:** None")
        
        if profile.get("dietary_restrictions"):
            st.write(f"**Dietary Restrictions:** {', '.join(profile['dietary_restrictions'])}")
        else:
            st.write("**Dietary Restrictions:** None")
        
        if profile.get("medical_conditions"):
            st.write(f"**Medical Conditions:** {', '.join(profile['medical_conditions'])}")
        else:
            st.write("**Medical Conditions:** None")
        
        # Edit profile option
        if st.button("Edit Profile"):
            st.session_state.edit_profile = True
        
        if st.session_state.get("edit_profile", False):
            st.subheader("Edit Profile")
            
            with st.form("edit_profile_form"):
                age = st.number_input("Age", min_value=1, max_value=120, value=profile["age"])
                gender = st.selectbox("Gender", ["Male", "Female", "Other"], index=["Male", "Female", "Other"].index(profile["gender"]))
                height = st.number_input("Height (cm)", min_value=1.0, value=profile["height"])
                weight = st.number_input("Weight (kg)", min_value=1.0, value=profile["weight"])
                
                diet_type = st.selectbox(
                    "Diet Type",
                    ["non-vegetarian", "vegetarian", "vegan"],
                    index=["non-vegetarian", "vegetarian", "vegan"].index(profile["diet_type"])
                )
                
                activity_level = st.selectbox(
                    "Activity Level",
                    ["sedentary", "light", "moderate", "active", "very-active"],
                    index=["sedentary", "light", "moderate", "active", "very-active"].index(profile["activity_level"])
                )
                
                health_goal = st.selectbox(
                    "Health Goal",
                    ["weight-loss", "weight-gain", "maintenance", "muscle-gain", "general-health"],
                    index=["weight-loss", "weight-gain", "maintenance", "muscle-gain", "general-health"].index(profile["health_goal"])
                )
                
                allergies = st.text_input("Allergies (comma-separated)", value=", ".join(profile.get("allergies", [])))
                dietary_restrictions = st.text_input("Dietary Restrictions (comma-separated)", value=", ".join(profile.get("dietary_restrictions", [])))
                medical_conditions = st.text_input("Medical Conditions (comma-separated)", value=", ".join(profile.get("medical_conditions", [])))
                
                submit_button = st.form_submit_button("Update Profile")
                
                if submit_button:
                    # Process form data
                    profile_data = {
                        "age": age,
                        "gender": gender,
                        "height": height,
                        "weight": weight,
                        "diet_type": diet_type,
                        "activity_level": activity_level,
                        "health_goal": health_goal,
                        "allergies": [item.strip() for item in allergies.split(",") if item.strip()],
                        "dietary_restrictions": [item.strip() for item in dietary_restrictions.split(",") if item.strip()],
                        "medical_conditions": [item.strip() for item in medical_conditions.split(",") if item.strip()]
                    }
                    
                    if update_profile(profile_data):
                        st.success("Profile updated successfully!")
                        st.session_state.edit_profile = False
                        time.sleep(1)
                        st.experimental_rerun()

def display_diet_requirements_page():
    st.header("Diet Requirements")
    
    user = st.session_state.user
    
    if not user.get("profile"):
        st.warning("Please create your profile first")
        return
    
    # Check if there are existing diet requirements
    diet_requirements = get_latest_diet_requirements()
    
    if diet_requirements:
        st.subheader("Your Latest Diet Requirements")
        st.write(f"Generated on: {diet_requirements['created_at']}")
        
        # Display daily requirements
        st.subheader("Daily Nutritional Requirements")
        
        for day, values in diet_requirements["daily_requirements"].items():
            with st.expander(f"{day.capitalize()}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Calories:** {values['calories']:.1f} kcal")
                    st.write(f"**Protein:** {values['protein']:.1f} g")
                    st.write(f"**Carbohydrates:** {values['carbohydrates']:.1f} g")
                with col2:
                    st.write(f"**Fat:** {values['fat']:.1f} g")
                    st.write(f"**Fiber:** {values['fiber']:.1f} g")
                    
                    # Safely handle optional fields
                    if "sugar" in values and values["sugar"] is not None:
                        st.write(f"**Sugar:** {values['sugar']:.1f} g")
                    
                    if "sodium" in values and values["sodium"] is not None:
                        st.write(f"**Sodium:** {values['sodium']:.1f} mg")
        
        # Display weekly average
        st.subheader("Weekly Average")
        weekly = diet_requirements["weekly_average"]
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Calories:** {weekly['calories']:.1f} kcal")
            st.write(f"**Protein:** {weekly['protein']:.1f} g")
            st.write(f"**Carbohydrates:** {weekly['carbohydrates']:.1f} g")
        with col2:
            st.write(f"**Fat:** {weekly['fat']:.1f} g")
            st.write(f"**Fiber:** {weekly['fiber']:.1f} g")
            
            # Safely handle optional fields
            if "sugar" in weekly and weekly["sugar"] is not None:
                st.write(f"**Sugar:** {weekly['sugar']:.1f} g")
            
            if "sodium" in weekly and weekly["sodium"] is not None:
                st.write(f"**Sodium:** {weekly['sodium']:.1f} mg")
    
    # Option to generate new diet requirements
    if st.button("Generate New Diet Requirements"):
        new_requirements = generate_diet_requirements()
        if new_requirements:
            st.success("Diet requirements generated successfully!")
            time.sleep(1)
            st.experimental_rerun()

def display_meal_recommendations_page():
    st.header("Meal Recommendations")
    
    user = st.session_state.user
    
    if not user.get("profile"):
        st.warning("Please create your profile first")
        return
    
    # Check if diet requirements exist
    diet_requirements = get_latest_diet_requirements()
    
    if not diet_requirements:
        st.warning("Please generate diet requirements first")
        return
    
    # Check if there are existing meal recommendations
    food_recommendation = get_latest_food_recommendation()
    
    if food_recommendation:
        st.subheader("Your Latest Meal Recommendations")
        st.write(f"Generated on: {food_recommendation['created_at']}")
        
        # Display meal plans for each day
        for day, plan in food_recommendation["meal_plans"].items():
            with st.expander(f"{day.capitalize()}"):
                st.write(f"**Total:** {plan['total_calories']:.1f} kcal, {plan['total_protein']:.1f}g protein, {plan['total_carbohydrates']:.1f}g carbs, {plan['total_fat']:.1f}g fat, {plan['total_fiber']:.1f}g fiber")
                
                if plan.get("notes"):
                    st.write(f"**Notes:** {plan['notes']}")
                
                for meal in plan["meals"]:
                    st.subheader(f"{meal['meal_type'].upper()}")
                    st.write(f"**Total:** {meal['total_calories']:.1f} kcal, {meal['total_protein']:.1f}g protein, {meal['total_carbohydrates']:.1f}g carbs, {meal['total_fat']:.1f}g fat, {meal['total_fiber']:.1f}g fiber")
                    
                    if meal.get("notes"):
                        st.write(f"**Notes:** {meal['notes']}")
                    
                    # Create a DataFrame for food items
                    food_items = []
                    for item in meal["food_items"]:
                        food_items.append({
                            "Food": f"{item['name']} ({item['quantity']})",
                            "Calories": f"{item['calories']:.1f} kcal",
                            "Protein": f"{item['protein']:.1f}g",
                            "Carbs": f"{item['carbohydrates']:.1f}g",
                            "Fat": f"{item['fat']:.1f}g",
                            "Fiber": f"{item['fiber']:.1f}g"
                        })
                    
                    if food_items:
                        df = pd.DataFrame(food_items)
                        st.table(df)
                        
                        # Display preparation notes if any
                        for item in meal["food_items"]:
                            if item.get("preparation_notes"):
                                st.write(f"**Preparation for {item['name']}:** {item['preparation_notes']}")
        
        # Display additional notes if any
        if food_recommendation.get("additional_notes"):
            st.subheader("Additional Notes")
            st.write(food_recommendation["additional_notes"])
        
        # Option to provide feedback
        st.subheader("Provide Feedback")
        feedback_text = st.text_area("Your feedback", key="feedback_text")
        feedback_type = st.selectbox(
            "Feedback Type",
            ["positive", "negative", "neutral"],
            key="feedback_type"
        )
        
        if st.button("Submit Feedback"):
            if feedback_text.strip():
                feedback = submit_feedback(
                    food_recommendation["id"],
                    feedback_text,
                    feedback_type
                )
                
                if feedback:
                    st.success("Feedback submitted successfully!")
                    
                    # If negative feedback with analysis, show the analysis
                    if feedback_type == "negative" and "analysis" in feedback:
                        st.subheader("Feedback Analysis")
                        
                        if "identified_concerns" in feedback["analysis"] and feedback["analysis"]["identified_concerns"]:
                            st.write("**Identified Concerns:**")
                            for concern in feedback["analysis"]["identified_concerns"]:
                                st.write(f"- {concern}")
                        
                        if "suggested_restrictions" in feedback["analysis"] and feedback["analysis"]["suggested_restrictions"]:
                            st.write("**Suggested Dietary Restrictions:**")
                            for restriction in feedback["analysis"]["suggested_restrictions"]:
                                st.write(f"- {restriction}")
                        
                        if "suggested_alternatives" in feedback["analysis"] and feedback["analysis"]["suggested_alternatives"]:
                            st.write("**Suggested Food Alternatives:**")
                            for food, alternatives in feedback["analysis"]["suggested_alternatives"].items():
                                st.write(f"- Instead of {food}, try: {', '.join(alternatives)}")
                        
                        if "recommendation" in feedback["analysis"] and feedback["analysis"]["recommendation"]:
                            st.write(f"**Recommendation:** {feedback['analysis']['recommendation']}")
            else:
                st.error("Feedback text cannot be empty")
    
    # Option to generate new meal recommendations
    st.subheader("Generate New Meal Recommendations")
    
    with st.form("generate_meal_form"):
        # Optional inputs
        st.write("**Food Availability (Optional)**")
        st.write("Enter available foods (comma-separated, leave empty to skip)")
        food_input = st.text_input("Available foods", key="food_input")
        
        st.write("**Meal Preferences (Optional)**")
        breakfast_input = st.text_input("Breakfast preferences (comma-separated)", key="breakfast_input")
        lunch_input = st.text_input("Lunch preferences (comma-separated)", key="lunch_input")
        dinner_input = st.text_input("Dinner preferences (comma-separated)", key="dinner_input")
        snack_input = st.text_input("Snack preferences (comma-separated)", key="snack_input")
        
        submit_button = st.form_submit_button("Generate Meal Recommendations")
        
        if submit_button:
            # Process inputs
            food_availability = None
            if food_input.strip():
                food_availability = [food.strip() for food in food_input.split(",") if food.strip()]
            
            meal_preferences = {}
            
            if breakfast_input.strip():
                meal_preferences["breakfast"] = [item.strip() for item in breakfast_input.split(",") if item.strip()]
            
            if lunch_input.strip():
                meal_preferences["lunch"] = [item.strip() for item in lunch_input.split(",") if item.strip()]
            
            if dinner_input.strip():
                meal_preferences["dinner"] = [item.strip() for item in dinner_input.split(",") if item.strip()]
            
            if snack_input.strip():
                meal_preferences["snack"] = [item.strip() for item in snack_input.split(",") if item.strip()]
            
            if not meal_preferences:
                meal_preferences = None
            
            # Generate meal recommendations
            new_recommendation = generate_food_recommendation(
                diet_requirements["id"],
                food_availability,
                meal_preferences
            )
            
            if new_recommendation:
                st.success("Meal recommendations generated successfully!")
                time.sleep(1)
                st.experimental_rerun()

def display_feedback_page():
    st.header("Feedback & Analysis")
    
    user = st.session_state.user
    
    if not user.get("profile"):
        st.warning("Please create your profile first")
        return
    
    # Get user feedbacks
    feedbacks = get_user_feedbacks()
    
    if not feedbacks or len(feedbacks) == 0:
        st.info("No feedback found. Please provide feedback on your meal recommendations.")
        return
    
    st.subheader("Your Feedback History")
    
    for feedback in feedbacks:
        with st.expander(f"Feedback from {feedback['created_at']}"):
            st.write(f"**Type:** {feedback['feedback_type']}")
            st.write(f"**Feedback:** {feedback['feedback_text']}")
            
            if "analysis" in feedback and feedback["analysis"]:
                analysis = feedback["analysis"]
                st.subheader("Analysis Results")
                
                if "identified_concerns" in analysis and analysis["identified_concerns"]:
                    st.write("**Identified Concerns:**")
                    for concern in analysis["identified_concerns"]:
                        st.write(f"- {concern}")
                
                if "suggested_restrictions" in analysis and analysis["suggested_restrictions"]:
                    st.write("**Suggested Dietary Restrictions:**")
                    for restriction in analysis["suggested_restrictions"]:
                        st.write(f"- {restriction}")
                
                if "suggested_alternatives" in analysis and analysis["suggested_alternatives"]:
                    st.write("**Suggested Food Alternatives:**")
                    for food, alternatives in analysis["suggested_alternatives"].items():
                        st.write(f"- Instead of {food}, try: {', '.join(alternatives)}")
                
                if "recommendation" in analysis and analysis["recommendation"]:
                    st.write(f"**Recommendation:** {analysis['recommendation']}")

# Main app
def main():
    # Initialize session state variables
    if "edit_profile" not in st.session_state:
        st.session_state.edit_profile = False
    
    # Display navigation sidebar
    sidebar_navigation()

if __name__ == "__main__":
    main()