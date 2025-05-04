from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List
import os
import uuid
import httpx
import base64
import json
import time
from pydantic import BaseModel
import replicate
import cloudflare
from cloudflare.client import CloudflareClient
from stytch.client import Client as StytchClient
import asyncio
import aiohttp
from openai import OpenAI
import tempfile
import subprocess
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="Anime Opening Generator API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development - restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize clients
openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
stytch_client = StytchClient(
    project_id=os.environ.get("STYTCH_PROJECT_ID"),
    secret=os.environ.get("STYTCH_SECRET")
)
cloudflare_client = CloudflareClient(
    api_key=os.environ.get("CLOUDFLARE_API_KEY"),
    email=os.environ.get("CLOUDFLARE_EMAIL")
)

# Constants
REPLICATE_API_TOKEN = os.environ.get("REPLICATE_API_TOKEN")
TEMP_DIR = "temp"
OUTPUT_DIR = "output"

# Ensure temp directories exist
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Response models
class VideoResponse(BaseModel):
    video_id: str
    video_url: str
    preview_url: str

# Helper functions
async def anime_transform_image(image_path, style="anime"):
    """Transform an image to anime style using Replicate"""
    client = replicate.Client(api_token=REPLICATE_API_TOKEN)
    
    # Using AnimeGANv2 model for transformation
    # In a real implementation, you might want to use a more advanced model
    model = "cjwbw/animegan2-pytorch:e4a3f2b729c29a6dc9a36590806b8c8294b0181d47c3c0942be9d8622f3a3960"
    
    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")
    
    output = client.run(
        model,
        input={
            "image": f"data:image/jpeg;base64,{image_data}"
        }
    )
    
    # The output is a URL to the transformed image
    return output

async def generate_narrative(num_people, theme):
    """Generate a narrative for the anime opening using OpenAI"""
    
    # Customize prompt based on theme
    theme_descriptions = {
        "action": "epic battle scenes with powerful poses and dramatic confrontations",
        "romance": "emotional moments with cherry blossoms and nostalgic scenery",
        "fantasy": "magical environments with mystical creatures and spell casting",
        "scifi": "futuristic cityscapes with neon lights and advanced technology",
        "comedy": "exaggerated expressions and funny slice-of-life situations"
    }
    
    theme_desc = theme_descriptions.get(theme, theme_descriptions["action"])
    
    prompt = f"""Create a short narrative script for an anime opening featuring {num_people} main characters. 
    The opening should be in the style of {theme} anime with {theme_desc}.
    
    Structure it with:
    1. A description of the setting/world
    2. Brief descriptions for each character and their signature poses/moments
    3. A sequence of key scenes for the opening (5-7 scenes)
    4. A concluding dramatic moment
    
    Keep it concise but vivid, focusing on visual elements that could be represented in a short video."""
    
    response = openai_client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are an expert anime screenwriter specializing in creating iconic opening sequences."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=1000,
        temperature=0.7
    )
    
    return response.choices[0].message.content

async def create_video_from_images(transformed_images, narrative, theme):
    """Create a video sequence using Cloudflare for processing"""
    
    # In a real implementation, we would:
    # 1. Use Cloudflare's Stream API to compose video
    # 2. Apply effects and transitions based on the theme
    # 3. Add background music
    # 4. Add text overlays for dramatic effect
    
    # For hackathon demo, we'll use a simplified version
    video_id = f"anime_opening_{uuid.uuid4()}"
    video_path = f"{OUTPUT_DIR}/{video_id}.mp4"
    
    # Choose music based on theme
    music_tracks = {
        "action": "assets/music/epic_battle.mp3",
        "romance": "assets/music/emotional_journey.mp3",
        "fantasy": "assets/music/magical_world.mp3",
        "scifi": "assets/music/cyberpunk_beats.mp3",
        "comedy": "assets/music/upbeat_fun.mp3"
    }
    
    music_track = music_tracks.get(theme, music_tracks["action"])
    
    # Generate video using ffmpeg (simplified for demo)
    # In production, we'd use Cloudflare Workers and Stream API
    
    # Create a temporary script for ffmpeg
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        for i, img in enumerate(transformed_images):
            # Each image shows for 2 seconds
            f.write(f"file '{img}'\n")
            f.write(f"duration 2\n")
        # The last image needs to be specified again without duration
        f.write(f"file '{transformed_images[-1]}'\n")
        concat_file = f.name
    
    # Generate video with ffmpeg
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", concat_file,
        "-i", music_track,
        "-c:v", "libx264", "-preset", "fast", "-crf", "22",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2",
        video_path
    ]
    
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Video creation failed: {str(e)}")
    
    # Upload to Cloudflare Stream (simulated for demo)
    video_url = f"https://example.com/stream/{video_id}"
    preview_url = f"https://example.com/stream/{video_id}/preview.jpg"
    
    os.unlink(concat_file)  # Clean up temp file
    
    return {
        "video_id": video_id,
        "video_url": video_url,
        "preview_url": preview_url
    }

@app.post("/api/generate-opening", response_model=VideoResponse)
async def generate_opening(
    images: List[UploadFile] = File(...),
    theme: str = Form("action")
):
    """Generate an anime opening from uploaded images"""
    
    if not images:
        raise HTTPException(status_code=400, detail="No images provided")
    
    if theme not in ["action", "romance", "fantasy", "scifi", "comedy"]:
        theme = "action"  # Default to action if invalid theme
    
    try:
        # Save uploaded images to temp directory
        saved_paths = []
        for i, img in enumerate(images):
            content = await img.read()
            save_path = f"{TEMP_DIR}/{uuid.uuid4()}.jpg"
            with open(save_path, "wb") as f:
                f.write(content)
            saved_paths.append(save_path)
        
        # Transform images to anime style (parallel processing)
        transformed_paths = []
        tasks = [anime_transform_image(path) for path in saved_paths]
        transformed_urls = await asyncio.gather(*tasks)
        
        # Download transformed images
        async with aiohttp.ClientSession() as session:
            for i, url in enumerate(transformed_urls):
                async with session.get(url) as response:
                    if response.status == 200:
                        transformed_path = f"{TEMP_DIR}/transformed_{i}.jpg"
                        with open(transformed_path, "wb") as f:
                            f.write(await response.read())
                        transformed_paths.append(transformed_path)
        
        # Generate narrative for the opening
        narrative = await generate_narrative(len(images), theme)
        
        # Create video from transformed images using Cloudflare
        video_result = await create_video_from_images(transformed_paths, narrative, theme)
        
        # Clean up temp files
        for path in saved_paths + transformed_paths:
            if os.path.exists(path):
                os.unlink(path)
        
        return video_result
    
    except Exception as e:
        # Log the error
        print(f"Error generating anime opening: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate anime opening: {str(e)}")

@app.post("/api/save-video")
async def save_video(
    video_id: str = Form(...),
    user_id: str = Form(...)
):
    """Save a generated video to user's account using Stytch"""
    
    # Verify user authentication
    try:
        # Check if the user exists in Stytch
        user_exists = True  # This would be a real Stytch API call
        
        if not user_exists:
            raise HTTPException(status_code=401, detail="Unauthorized")
        
        # Save video reference to user's account
        # In a production app, this would update a database
        
        return {"success": True, "message": "Video saved successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save video: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": time.time()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)