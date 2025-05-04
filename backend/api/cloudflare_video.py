import os
import json
import time
import uuid
import asyncio
import subprocess
import tempfile
from typing import List, Dict, Any, Optional
import httpx
from PIL import Image, ImageDraw, ImageFont

class AnimeVideoGenerator:
    """Class for composing anime openings using Cloudflare Stream and Workers"""
    
    def __init__(self, api_key=None, account_id=None):
        self.api_key = api_key or os.environ.get("CLOUDFLARE_API_KEY")
        self.account_id = account_id or os.environ.get("CLOUDFLARE_ACCOUNT_ID")
        self.base_url = f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/stream"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.temp_dir = "temp_video"
        self.output_dir = "output_videos"
        
        # Ensure directories exist
        os.makedirs(self.temp_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Map of theme to music tracks
        self.music_tracks = {
            "action": "assets/music/epic_battle.mp3",
            "romance": "assets/music/emotional_journey.mp3",
            "fantasy": "assets/music/magical_world.mp3",
            "scifi": "assets/music/cyberpunk_beats.mp3",
            "comedy": "assets/music/upbeat_fun.mp3"
        }
        
        # Map of theme to transitions
        self.transitions = {
            "action": ["fade", "wipe_left", "dissolve", "flash", "slide"],
            "romance": ["fade", "dissolve", "blur", "fade_to_white", "slide"],
            "fantasy": ["dissolve", "glow", "sparkle", "fade", "zoom"],
            "scifi": ["glitch", "digital", "slide", "matrix", "flash"],
            "comedy": ["bounce", "pop", "slide", "zoom", "wipe_circle"]
        }
    
    async def create_cloudflare_video(self, video_path: str, title: str) -> Dict[str, Any]:
        """
        Upload a video to Cloudflare Stream.
        
        Args:
            video_path: Path to the local video file
            title: Title for the video
            
        Returns:
            Dict with video ID and URLs
        """
        try:
            # For a real implementation, we would use Cloudflare's API
            # For hackathon demo, we'll simulate the response
            video_id = f"anime_opening_{uuid.uuid4()}"
            
            # Simulate API call delay
            await asyncio.sleep(2)
            
            return {
                "success": True,
                "result": {
                    "uid": video_id,
                    "playback": {
                        "hls": f"https://example.com/stream/{video_id}/manifest.m3u8",
                        "dash": f"https://example.com/stream/{video_id}/manifest.mpd"
                    },
                    "preview": f"https://example.com/stream/{video_id}/preview.jpg",
                    "thumbnail": f"https://example.com/stream/{video_id}/thumbnail.jpg"
                }
            }
            
            # Real implementation would look like:
            """
            async with httpx.AsyncClient() as client:
                with open(video_path, "rb") as f:
                    files = {"file": f}
                    data = {"meta": json.dumps({"name": title})}
                    
                    response = await client.post(
                        f"{self.base_url}",
                        headers=self.headers,
                        files=files,
                        data=data
                    )
                    
                    if response.status_code == 200:
                        return response.json()
                    else:
                        raise Exception(f"Upload failed: {response.text}")
            """
        
        except Exception as e:
            print(f"Error uploading to Cloudflare Stream: {str(e)}")
            raise
    
    async def apply_transition(self, image1_path: str, image2_path: str, transition_type: str, output_path: str) -> str:
        """
        Apply a transition effect between two images.
        
        Args:
            image1_path: Path to the first image
            image2_path: Path to the second image
            transition_type: Type of transition effect
            output_path: Path to save the output image sequence
            
        Returns:
            Path to the transition image sequence
        """
        # This would be implemented using Cloudflare Workers or ffmpeg
        # For demo, we'll use ffmpeg for transitions
        try:
            os.makedirs(output_path, exist_ok=True)
            
            # Different ffmpeg commands for different transitions
            if transition_type == "fade":
                cmd = [
                    "ffmpeg", "-y",
                    "-loop", "1", "-t", "1", "-i", image1_path,
                    "-loop", "1", "-t", "1", "-i", image2_path,
                    "-filter_complex", "xfade=transition=fade:duration=1:offset=0",
                    "-vframes", "30",
                    f"{output_path}/frame%03d.png"
                ]
            elif transition_type == "wipe_left":
                cmd = [
                    "ffmpeg", "-y",
                    "-loop", "1", "-t", "1", "-i", image1_path,
                    "-loop", "1", "-t", "1", "-i", image2_path,
                    "-filter_complex", "xfade=transition=wipeleft:duration=1:offset=0",
                    "-vframes", "30",
                    f"{output_path}/frame%03d.png"
                ]
            elif transition_type == "dissolve":
                cmd = [
                    "ffmpeg", "-y",
                    "-loop", "1", "-t", "1", "-i", image1_path,
                    "-loop", "1", "-t", "1", "-i", image2_path,
                    "-filter_complex", "xfade=transition=dissolve:duration=1:offset=0",
                    "-vframes", "30",
                    f"{output_path}/frame%03d.png"
                ]
            elif transition_type == "flash":
                cmd = [
                    "ffmpeg", "-y",
                    "-loop", "1", "-t", "0.5", "-i", image1_path,
                    "-loop", "1", "-t", "0.5", "-i", image2_path,
                    "-filter_complex", "[0:v]fade=t=out:st=0.3:d=0.2[v0];[1:v]fade=t=in:st=0:d=0.2[v1];[v0][v1]concat=n=2:v=1:a=0",
                    "-vframes", "30",
                    f"{output_path}/frame%03d.png"
                ]
            else:
                # Default to simple fade
                cmd = [
                    "ffmpeg", "-y",
                    "-loop", "1", "-t", "1", "-i", image1_path,
                    "-loop", "1", "-t", "1", "-i", image2_path,
                    "-filter_complex", "xfade=transition=fade:duration=1:offset=0",
                    "-vframes", "30",
                    f"{output_path}/frame%03d.png"
                ]
            
            subprocess.run(cmd, check=True)
            return output_path
            
        except Exception as e:
            print(f"Error applying transition: {str(e)}")
            # Fallback to no transition
            return None
    
    async def add_text_overlay(self, image_path: str, text: str, position: str = "bottom", font_size: int = 36) -> str:
        """
        Add text overlay to an image.
        
        Args:
            image_path: Path to the image
            text: Text to overlay
            position: Position of the text (top, bottom, center)
            font_size: Font size
            
        Returns:
            Path to the new image with text
        """
        try:
            img = Image.open(image_path)
            draw = ImageDraw.Draw(img)
            
            # Use a default font if custom font not available
            try:
                font = ImageFont.truetype("assets/fonts/anime.ttf", font_size)
            except:
                font = ImageFont.load_default()
            
            # Calculate position
            width, height = img.size
            text_width, text_height = draw.textsize(text, font=font)
            
            if position == "top":
                text_position = ((width - text_width) // 2, 20)
            elif position == "bottom":
                text_position = ((width - text_width) // 2, height - text_height - 20)
            else:  # center
                text_position = ((width - text_width) // 2, (height - text_height) // 2)
            
            # Add shadow for better visibility
            shadow_color = "black"
            shadow_offset = 2
            draw.text((text_position[0] + shadow_offset, text_position[1] + shadow_offset), text, font=font, fill=shadow_color)
            
            # Draw the main text
            draw.text(text_position, text, font=font, fill="white")
            
            # Save the image with text
            output_path = f"{self.temp_dir}/text_{uuid.uuid4()}.png"
            img.save(output_path)
            
            return output_path
            
        except Exception as e:
            print(f"Error adding text overlay: {str(e)}")
            return image_path  # Return original image as fallback
    
    async def create_anime_opening(
        self,
        transformed_images: List[str],
        narrative: Dict[str, Any],
        theme: str,
        output_filename: str = None
    ) -> str:
        """
        Create a complete anime opening video.
        
        Args:
            transformed_images: List of paths to transformed character images
            narrative: Narrative structure for the opening
            theme: Theme/style of the anime opening
            output_filename: Custom filename for the output video
            
        Returns:
            Path to the generated video
        """
        try:
            if not output_filename:
                output_filename = f"anime_opening_{uuid.uuid4()}.mp4"
            
            output_path = os.path.join(self.output_dir, output_filename)
            
            # Select music track based on theme
            music_track = self.music_tracks.get(theme, self.music_tracks["action"])
            
            # Get transitions for this theme
            theme_transitions = self.transitions.get(theme, self.transitions["action"])
            
            # Create temporary script for ffmpeg
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
                concat_file = f.name
                
                # Process each scene from the narrative
                scenes = narrative.get("scenes", [])
                
                if not scenes:
                    # If no scenes defined, create simple sequence of images
                    for i, img in enumerate(transformed_images):
                        # Each image shows for 2 seconds
                        f.write(f"file '{img}'\n")
                        f.write(f"duration 2\n")
                else:
                    # Create specific scenes based on narrative
                    for i, scene in enumerate(scenes):
                        # Select appropriate image(s) for this scene
                        if i < len(transformed_images):
                            img_path = transformed_images[i]
                        else:
                            # Reuse images if we have more scenes than images
                            img_path = transformed_images[i % len(transformed_images)]
                        
                        # Add text descriptions if available
                        scene_desc = scene.get("description", "")
                        if scene_desc:
                            img_path = await self.add_text_overlay(img_path, scene_desc)
                        
                        # Add to concat file
                        scene_duration = 2  # Default 2 seconds per scene
                        f.write(f"file '{img_path}'\n")
                        f.write(f"duration {scene_duration}\n")
                
                # The last image needs to be specified again without duration
                last_img = transformed_images[-1] if transformed_images else img_path
                f.write(f"file '{last_img}'\n")
            
            # Add title frame
            title = narrative.get("title", "Anime Opening")
            title_background = f"{self.temp_dir}/title_bg.png"
            
            # Create a black background for title
            title_img = Image.new('RGB', (1920, 1080), color='black')
            title_img.save(title_background)
            
            title_frame = await self.add_text_overlay(title_background, title, position="center", font_size=72)
            
            # Create final video with ffmpeg
            cmd = [
                "ffmpeg", "-y",
                "-f", "concat", "-safe", "0", "-i", concat_file,
                "-i", title_frame,
                "-i", music_track,
                "-filter_complex", "[0:v][1:v]concat=n=2:v=1:a=0[v]",
                "-map", "[v]", "-map", "2:a",
                "-c:v", "libx264", "-preset", "fast", "-crf", "22",
                "-c:a", "aac", "-b:a", "192k",
                "-shortest",
                "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2",
                output_path
            ]
            
            subprocess.run(cmd, check=True)
            
            # Upload to Cloudflare Stream
            cf_result = await self.create_cloudflare_video(output_path, title)
            
            # Cleanup temp files
            os.unlink(concat_file)
            
            # Return both local path and Cloudflare stream info
            return {
                "local_path": output_path,
                "cloudflare": cf_result
            }
            
        except Exception as e:
            print(f"Error creating anime opening: {str(e)}")
            raise
    
    async def apply_visual_effects(self, image_path: str, effect_type: str) -> str:
        """
        Apply anime-style visual effects to an image.
        
        Args:
            image_path: Path to the image
            effect_type: Type of effect to apply
            
        Returns:
            Path to the processed image
        """
        # This would use Cloudflare Workers or image processing libraries
        # For demo, we'll use simple PIL effects
        try:
            img = Image.open(image_path)
            output_path = f"{self.temp_dir}/effect_{uuid.uuid4()}.png"
            
            if effect_type == "speed_lines":
                # Simulate speed lines (simplified for demo)
                draw = ImageDraw.Draw(img)
                width, height = img.size
                center_x, center_y = width // 2, height // 2
                
                for i in range(50):
                    line_length = np.random.randint(50, 200)
                    angle = np.random.random() * 2 * np.pi
                    start_x = center_x + int(np.cos(angle) * 100)
                    start_y = center_y + int(np.sin(angle) * 100)
                    end_x = start_x + int(np.cos(angle) * line_length)
                    end_y = start_y + int(np.sin(angle) * line_length)
                    
                    draw.line([(start_x, start_y), (end_x, end_y)], fill="white", width=2)
                
            elif effect_type == "glow":
                # Simple glow effect
                from PIL import ImageFilter
                img = img.filter(ImageFilter.GaussianBlur(radius=2))
                
            elif effect_type == "zoom_blur":
                # Zoom blur effect
                from PIL import ImageFilter
                img_blurred = img.filter(ImageFilter.GaussianBlur(radius=5))
                img_small = img.resize((img.width // 2, img.height // 2))
                img_small = img_small.resize(img.size)
                img = Image.blend(img_small, img_blurred, 0.5)
                
            else:
                # No effect, return original
                return image_path
            
            img.save(output_path)
            return output_path
            
        except Exception as e:
            print(f"Error applying visual effect: {str(e)}")
            return image_path  # Return original as fallback

# Example usage
async def main():
    generator = AnimeVideoGenerator()
    
    # Example: Create an anime opening from transformed images and narrative
    transformed_images = [
        "transformed_images/char1.png",
        "transformed_images/char2.png",
        "transformed_images/char3.png"
    ]
    
    narrative = {
        "title": "Cosmic Legends",
        "theme": "action",
        "scenes": [
            {"description": "A world on the brink of chaos"},
            {"description": "Three heroes emerge from the shadows"},
            {"description": "A battle of epic proportions begins"},
            {"description": "Will they save the world?"}
        ]
    }
    
    result = await generator.create_anime_opening(
        transformed_images=transformed_images,
        narrative=narrative,
        theme="action"
    )
    
    print(f"Anime opening created: {result}")

if __name__ == "__main__":
    asyncio.run(main())