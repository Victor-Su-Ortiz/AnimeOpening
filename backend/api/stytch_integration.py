import os
import json
import time
import uuid
import asyncio
from typing import Dict, List, Any, Optional
import httpx
from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

# Mock database for hackathon demo
USERS_DB = {}
OPENINGS_DB = {}

# Define models
class UserCreate(BaseModel):
    email: str
    
class User(BaseModel):
    id: str
    email: str
    created_at: int
    
class AnimeOpening(BaseModel):
    id: str
    user_id: str
    title: str
    theme: str
    video_url: str
    preview_url: str
    created_at: int
    
class OpeningSave(BaseModel):
    title: str
    theme: str
    video_url: str
    preview_url: str

class StytchService:
    """Service for handling Stytch authentication and user management"""
    
    def __init__(self, project_id=None, secret=None):
        self.project_id = project_id or os.environ.get("STYTCH_PROJECT_ID")
        self.secret = secret or os.environ.get("STYTCH_SECRET")
        self.api_url = "https://api.stytch.com/v1"
        self.auth = httpx.BasicAuth(self.project_id, self.secret)
    
    async def authenticate_token(self, session_token: str) -> Dict[str, Any]:
        """
        Authenticate a session token with Stytch.
        
        Args:
            session_token: The Stytch session token
            
        Returns:
            Dict containing user information if valid
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_url}/sessions/authenticate",
                    auth=self.auth,
                    json={"session_token": session_token}
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    print(f"Stytch authentication error: {response.text}")
                    raise HTTPException(status_code=401, detail="Invalid authentication token")
        
        except Exception as e:
            print(f"Error authenticating token: {str(e)}")
            raise HTTPException(status_code=500, detail="Authentication service error")
    
    async def create_user(self, email: str) -> Dict[str, Any]:
        """
        Create a new user in Stytch.
        
        Args:
            email: User's email address
            
        Returns:
            Dict containing the created user information
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_url}/users",
                    auth=self.auth,
                    json={"email": email}
                )
                
                if response.status_code == 201:
                    return response.json()
                else:
                    print(f"Stytch user creation error: {response.text}")
                    raise HTTPException(status_code=400, detail="Failed to create user")
        
        except Exception as e:
            print(f"Error creating user: {str(e)}")
            raise HTTPException(status_code=500, detail="User creation service error")
    
    async def send_magic_link(self, email: str, redirect_url: str) -> Dict[str, Any]:
        """
        Send a magic link to the user's email.
        
        Args:
            email: User's email address
            redirect_url: URL to redirect after authentication
            
        Returns:
            Dict containing the response from Stytch
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_url}/magic_links/email/login_or_create",
                    auth=self.auth,
                    json={
                        "email": email,
                        "login_magic_link_url": redirect_url,
                        "signup_magic_link_url": redirect_url
                    }
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    print(f"Stytch magic link error: {response.text}")
                    raise HTTPException(status_code=400, detail="Failed to send magic link")
        
        except Exception as e:
            print(f"Error sending magic link: {str(e)}")
            raise HTTPException(status_code=500, detail="Magic link service error")
    
    async def revoke_session(self, session_token: str) -> Dict[str, Any]:
        """
        Revoke a session token.
        
        Args:
            session_token: The Stytch session token to revoke
            
        Returns:
            Dict containing the response from Stytch
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_url}/sessions/revoke",
                    auth=self.auth,
                    json={"session_token": session_token}
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    print(f"Stytch session revocation error: {response.text}")
                    raise HTTPException(status_code=400, detail="Failed to revoke session")
        
        except Exception as e:
            print(f"Error revoking session: {str(e)}")
            raise HTTPException(status_code=500, detail="Session revocation service error")

# For hackathon demo, we'll create a mock implementation
class MockStytchService:
    """Mock implementation of StytchService for hackathon demo"""
    
    async def authenticate_token(self, session_token: str) -> Dict[str, Any]:
        """Mock token authentication"""
        # In the real implementation, this would validate with Stytch
        if session_token == "invalid_token":
            raise HTTPException(status_code=401, detail="Invalid authentication token")
        
        # For demo, we'll accept any non-"invalid" token and return a mock user
        user_id = session_token.split("_")[-1] if "_" in session_token else "user123"
        
        if user_id not in USERS_DB:
            # Create a mock user if not exists
            USERS_DB[user_id] = {
                "id": user_id,
                "email": f"user{user_id}@example.com",
                "created_at": int(time.time())
            }
        
        return {
            "status_code": 200,
            "user_id": user_id,
            "user": USERS_DB[user_id]
        }
    
    async def create_user(self, email: str) -> Dict[str, Any]:
        """Mock user creation"""
        user_id = f"user_{uuid.uuid4()}"
        user = {
            "id": user_id,
            "email": email,
            "created_at": int(time.time())
        }
        USERS_DB[user_id] = user
        
        return {
            "status_code": 201,
            "user_id": user_id,
            "user": user
        }
    
    async def send_magic_link(self, email: str, redirect_url: str) -> Dict[str, Any]:
        """Mock magic link sending"""
        return {
            "status_code": 200,
            "email_id": f"email_{uuid.uuid4()}",
            "user_id": f"user_{uuid.uuid4()}",
            "message": f"Magic link would be sent to {email} in production"
        }
    
    async def revoke_session(self, session_token: str) -> Dict[str, Any]:
        """Mock session revocation"""
        return {
            "status_code": 200,
            "message": "Session revoked successfully"
        }

# API for Anime Opening Storage
class AnimeOpeningService:
    """Service for managing user's anime openings"""
    
    def __init__(self, stytch_service):
        self.stytch_service = stytch_service
    
    async def get_user_openings(self, user_id: str) -> List[AnimeOpening]:
        """
        Get all anime openings for a user.
        
        Args:
            user_id: The user's ID
            
        Returns:
            List of the user's anime openings
        """
        # In a real implementation, this would query a database
        user_openings = []
        for opening_id, opening in OPENINGS_DB.items():
            if opening.get("user_id") == user_id:
                user_openings.append(opening)
        
        return user_openings
    
    async def get_opening(self, opening_id: str) -> Optional[AnimeOpening]:
        """
        Get a specific anime opening.
        
        Args:
            opening_id: The opening's ID
            
        Returns:
            The anime opening if found, None otherwise
        """
        return OPENINGS_DB.get(opening_id)
    
    async def save_opening(self, user_id: str, opening_data: OpeningSave) -> AnimeOpening:
        """
        Save a new anime opening for a user.
        
        Args:
            user_id: The user's ID
            opening_data: Data for the new anime opening
            
        Returns:
            The saved anime opening
        """
        opening_id = f"opening_{uuid.uuid4()}"
        
        opening = {
            "id": opening_id,
            "user_id": user_id,
            "title": opening_data.title,
            "theme": opening_data.theme,
            "video_url": opening_data.video_url,
            "preview_url": opening_data.preview_url,
            "created_at": int(time.time())
        }
        
        # In a real implementation, this would save to a database
        OPENINGS_DB[opening_id] = opening
        
        return opening
    
    async def delete_opening(self, opening_id: str, user_id: str) -> bool:
        """
        Delete an anime opening.
        
        Args:
            opening_id: The opening's ID
            user_id: The user's ID (for authorization)
            
        Returns:
            True if the opening was deleted, False otherwise
        """
        opening = OPENINGS_DB.get(opening_id)
        
        if not opening:
            return False
        
        if opening.get("user_id") != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this opening")
        
        # Delete the opening
        del OPENINGS_DB[opening_id]
        
        return True

# FastAPI implementation
app = FastAPI(title="Anime Opening Storage API")
security = HTTPBearer()

# Choose the appropriate implementation
if os.environ.get("ENVIRONMENT") == "production":
    stytch_service = StytchService()
else:
    stytch_service = MockStytchService()

opening_service = AnimeOpeningService(stytch_service)

# Authentication dependency
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Dependency to get the current authenticated user.
    
    Args:
        credentials: HTTP Authorization credentials
        
    Returns:
        Dict containing the authenticated user information
    """
    try:
        token = credentials.credentials
        auth_result = await stytch_service.authenticate_token(token)
        return auth_result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")

# API Routes
@app.post("/auth/magic-link")
async def send_magic_link(user: UserCreate):
    """Send a magic link for authentication"""
    redirect_url = "https://animeopeninggenerator.example.com/auth/callback"
    result = await stytch_service.send_magic_link(user.email, redirect_url)
    return {"message": "Magic link sent successfully", "email": user.email}

@app.post("/auth/logout")
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Logout the current user"""
    token = credentials.credentials
    result = await stytch_service.revoke_session(token)
    return {"message": "Logged out successfully"}

@app.get("/openings")
async def get_openings(current_user: Dict = Depends(get_current_user)):
    """Get all openings for the current user"""
    user_id = current_user.get("user_id")
    openings = await opening_service.get_user_openings(user_id)
    return {"openings": openings}

@app.get("/openings/{opening_id}")
async def get_opening(opening_id: str, current_user: Dict = Depends(get_current_user)):
    """Get a specific opening"""
    opening = await opening_service.get_opening(opening_id)
    
    if not opening:
        raise HTTPException(status_code=404, detail="Opening not found")
    
    # Check if user owns this opening
    if opening.get("user_id") != current_user.get("user_id"):
        raise HTTPException(status_code=403, detail="Not authorized to access this opening")
    
    return opening

@app.post("/openings")
async def save_opening(opening_data: OpeningSave, current_user: Dict = Depends(get_current_user)):
    """Save a new opening"""
    user_id = current_user.get("user_id")
    opening = await opening_service.save_opening(user_id, opening_data)
    return opening

@app.delete("/openings/{opening_id}")
async def delete_opening(opening_id: str, current_user: Dict = Depends(get_current_user)):
    """Delete an opening"""
    user_id = current_user.get("user_id")
    result = await opening_service.delete_opening(opening_id, user_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="Opening not found")
    
    return {"message": "Opening deleted successfully"}