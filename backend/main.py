import os
import sys
import asyncio
import uuid
import logging
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from typing import List, Dict, Any, Optional
import json
from pydantic import BaseModel
import time

# Import our custom components
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from api.replicate_transforms import AnimeImageTransformer
from api.openai_narrative import AnimeNarrativeGenerator
from api.cloudflare_video import AnimeVideoGenerator
from api.stytch_integration import MockStytchService, get_current_user

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Anime Opening Generator")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development - restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize our services
image_transformer = AnimeImageTransformer()
narrative_generator = AnimeNarrativeGenerator()
video_generator = AnimeVideoGenerator()

# Status tracking for long-running tasks
generation_tasks = {}

# Request/Response models
class GenerationRequest(BaseModel):
    theme: str
    title: Optional[str] = None
    character_descriptions: Optional[List[str]] = None

class GenerationStatus(BaseModel):
    task_id: str
    status: str
    progress: int
    message: str
    result: Optional[Dict[str, Any]] = None

class SaveOpeningRequest(BaseModel):
    opening_id: str
    title: str

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/output_videos", StaticFiles(directory="output_videos"), name="output_videos")

# API Routes
@app.get("/")
async def root():
    return {"message": "Anime Opening Generator API"}

@app.post("/api/generate-opening", response_model=GenerationStatus)
async def generate_opening(
    background_tasks: BackgroundTasks,
    theme: str = Form("action"),
    title: Optional[str] = Form(None),
    images: List[UploadFile] = File(...),
    current_user: Dict = Depends(get_current_user)
):
    """
    Start the generation of an anime opening.
    This is an asynchronous process, so it returns a task ID for tracking.
    """
    if not images:
        raise HTTPException(status_code=400, detail="No images provided")
    
    if theme not in ["action", "romance", "fantasy", "scifi", "comedy"]:
        theme = "action"  # Default to action if invalid theme
    
    try:
        # Generate a unique task ID
        task_id = str(uuid.uuid4())
        
        # Create a temporary directory for this task
        task_dir = f"temp/{task_id}"
        os.makedirs(task_dir, exist_ok=True)
        
        # Save uploaded images to the task directory
        saved_paths = []
        for i, img in enumerate(images):
            content = await img.read()
            save_path = f"{task_dir}/original_{i}.jpg"
            with open(save_path, "wb") as f:
                f.write(content)
            saved_paths.append(save_path)
        
        # Initialize the task status
        generation_tasks[task_id] = {
            "status": "started",
            "progress": 0,
            "message": "Generation started",
            "result": None,
            "start_time": time.time(),
            "user_id": current_user.get("user_id")
        }
        
        # Start the generation process in the background
        background_tasks.add_task(
            process_generation,
            task_id=task_id,
            saved_paths=saved_paths,
            theme=theme,
            title=title
        )
        
        return GenerationStatus(
            task_id=task_id,
            status="started",
            progress=0,
            message="Generation started",
            result=None
        )
        
    except Exception as e:
        logger.error(f"Error starting generation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start generation: {str(e)}")

@app.get("/api/generation-status/{task_id}", response_model=GenerationStatus)
async def get_generation_status(task_id: str):
    """
    Get the status of a generation task.
    """
    if task_id not in generation_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task_info = generation_tasks[task_id]
    
    return GenerationStatus(
        task_id=task_id,
        status=task_info["status"],
        progress=task_info["progress"],
        message=task_info["message"],
        result=task_info["result"]
    )

@app.post("/api/save-opening")
async def save_opening(request: SaveOpeningRequest, current_user: Dict = Depends(get_current_user)):
    """
    Save a generated opening to the user's account.
    """
    # In a real implementation, this would save to a database
    # For the hackathon demo, we'll just return success
    return {
        "success": True,
        "message": "Opening saved successfully",
        "opening_id": request.opening_id
    }

@app.get("/api/openings")
async def get_user_openings(current_user: Dict = Depends(get_current_user)):
    """
    Get all openings for the current user.
    """
    # In a real implementation, this would query a database
    # For the hackathon demo, we'll return mock data
    return {
        "openings": [
            {
                "id": "opening_1",
                "title": "My First Anime Opening",
                "theme": "action",
                "preview_url": "/static/previews/preview1.jpg",
                "video_url": "/output_videos/anime_opening_1.mp4",
                "created_at": int(time.time()) - 3600
            }
        ]
    }

# Background processing function
async def process_generation(task_id: str, saved_paths: List[str], theme: str, title: Optional[str]):
    """
    Process the generation of an anime opening in the background.
    """
    try:
        # Update task status
        update_task_status(task_id, "processing", 10, "Transforming images to anime style")
        
        # Transform images to anime style
        transformed_paths = await image_transformer.batch_transform(saved_paths, theme)
        
        # Update task status
        update_task_status(task_id, "processing", 30, "Generating narrative")
        
        # Generate narrative
        narrative = await narrative_generator.generate_opening_narrative(
            num_characters=len(saved_paths),
            theme=theme,
            title=title
        )
        
        # Update task status
        update_task_status(task_id, "processing", 50, "Generating detailed scenes")
        
        # Generate detailed scenes
        detailed_scenes = await narrative_generator.generate_scene_descriptions(narrative)
        narrative["scenes"] = detailed_scenes
        
        # Update task status
        update_task_status(task_id, "processing", 70, "Creating video")
        
        # Generate video
        video_result = await video_generator.create_anime_opening(
            transformed_images=transformed_paths,
            narrative=narrative,
            theme=theme,
            output_filename=f"anime_opening_{task_id}.mp4"
        )
        
        # Update task status with result
        update_task_status(
            task_id, 
            "completed", 
            100, 
            "Opening generated successfully",
            {
                "video_path": video_result["local_path"],
                "video_url": f"/output_videos/anime_opening_{task_id}.mp4",
                "preview_url": f"/static/previews/preview_{task_id}.jpg",
                "narrative": narrative,
                "theme": theme,
                "id": task_id
            }
        )
        
        # Clean up temporary files
        for path in saved_paths + transformed_paths:
            if os.path.exists(path):
                os.unlink(path)
        
    except Exception as e:
        logger.error(f"Error in generation process: {str(e)}")
        update_task_status(task_id, "failed", 0, f"Generation failed: {str(e)}")

def update_task_status(task_id: str, status: str, progress: int, message: str, result: Dict[str, Any] = None):
    """
    Update the status of a generation task.
    """
    if task_id in generation_tasks:
        generation_tasks[task_id].update({
            "status": status,
            "progress": progress,
            "message": message,
            "last_updated": time.time()
        })
        
        if result:
            generation_tasks[task_id]["result"] = result

# Clean up old tasks periodically
@app.on_event("startup")
@app.on_event("shutdown")
async def cleanup_tasks():
    """
    Clean up old generation tasks to prevent memory leaks.
    """
    current_time = time.time()
    to_remove = []
    
    for task_id, task_info in generation_tasks.items():
        # Remove tasks older than 1 hour
        if current_time - task_info.get("start_time", 0) > 3600:
            to_remove.append(task_id)
    
    for task_id in to_remove:
        del generation_tasks[task_id]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)