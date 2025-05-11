# Database utility file for MongoDB connection
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

class Database:
    client = None
    db = None

    @classmethod
    async def connect_db(cls):
        """Connect to MongoDB database"""
        # First check if MongoDB URL is set in environment
        mongo_uri = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
        db_name = os.getenv("DATABASE_NAME", "virtual_dietician")
        
        print(f"Connecting to MongoDB at: {mongo_uri}")
        
        try:
            cls.client = AsyncIOMotorClient(mongo_uri)
            cls.db = cls.client[db_name]
            print(f"Connected to MongoDB database: {db_name}")
            return cls.db
        except Exception as e:
            print(f"Failed to connect to MongoDB: {str(e)}")
            raise
    
    @classmethod
    async def close_db_connection(cls):
        """Close MongoDB connection"""
        if cls.client is not None:
            cls.client.close()
            print("MongoDB connection closed")

# Get specific collections
async def get_user_collection():
    db = await Database.connect_db()
    return db.users

async def get_diet_plan_collection():
    db = await Database.connect_db()
    return db.diet_plans

async def get_food_recommendation_collection():
    db = await Database.connect_db()
    return db.food_recommendations

async def get_feedback_collection():
    db = await Database.connect_db()
    return db.feedback

async def get_special_needs_collection():
    db = await Database.connect_db()
    return db.special_needs