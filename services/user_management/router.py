from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import sys
sys.path.append("../..")
from services.shared.database import get_user_collection
from .models import UserCreate, UserLogin, UserProfile, UserProfileUpdate, User
from .auth import create_access_token, get_password_hash, verify_password, get_current_user
from datetime import datetime
from bson import ObjectId
from typing import List

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Auth endpoint
@router.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user_collection = await get_user_collection()
    user = await user_collection.find_one({"email": form_data.username})
    
    if not user or not verify_password(form_data.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": str(user["_id"])})
    return {"access_token": access_token, "token_type": "bearer"}

# User endpoints
@router.post("/users/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate):
    user_collection = await get_user_collection()
    
    # Check if user already exists
    existing_user = await user_collection.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash password
    hashed_password = get_password_hash(user_data.password)
    
    now = datetime.utcnow()
    user_dict = {
        "email": user_data.email,
        "name": user_data.name,
        "password": hashed_password,
        "created_at": now,
        "updated_at": now
    }
    
    result = await user_collection.insert_one(user_dict)
    
    created_user = await user_collection.find_one({"_id": result.inserted_id})
    created_user["id"] = str(created_user.pop("_id"))
    
    return created_user

@router.post("/users/profile", response_model=User)
async def create_user_profile(
    profile_data: UserProfile, 
    current_user: User = Depends(get_current_user)
):
    user_collection = await get_user_collection()
    user_id = ObjectId(current_user["id"])
    
    profile_dict = profile_data.dict()
    
    await user_collection.update_one(
        {"_id": user_id},
        {
            "$set": {
                "profile": profile_dict,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    updated_user = await user_collection.find_one({"_id": user_id})
    updated_user["id"] = str(updated_user.pop("_id"))
    
    return updated_user

@router.put("/users/profile", response_model=User)
async def update_user_profile(
    profile_update: UserProfileUpdate,
    current_user: User = Depends(get_current_user)
):
    user_collection = await get_user_collection()
    user_id = ObjectId(current_user["id"])
    
    # Get existing profile
    user = await user_collection.find_one({"_id": user_id})
    if not user.get("profile"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Profile not found. Create a profile first."
        )
    
    # Update only provided fields
    update_dict = {}
    for field, value in profile_update.dict(exclude_unset=True).items():
        if value is not None:
            update_dict[f"profile.{field}"] = value
    
    update_dict["updated_at"] = datetime.utcnow()
    
    await user_collection.update_one(
        {"_id": user_id},
        {"$set": update_dict}
    )
    
    updated_user = await user_collection.find_one({"_id": user_id})
    updated_user["id"] = str(updated_user.pop("_id"))
    
    return updated_user

@router.get("/users/me", response_model=User)
async def get_user_profile(current_user: User = Depends(get_current_user)):
    return current_user