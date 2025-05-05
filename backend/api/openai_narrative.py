import os
import json
import asyncio
from openai import OpenAI
from typing import List, Dict, Any, Optional

class AnimeNarrativeGenerator:
    """Class to generate anime opening narratives using OpenAI"""
    
    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.client = OpenAI(api_key=self.api_key)
    
    async def generate_opening_narrative(
        self, 
        num_characters: int,
        theme: str,
        character_descriptions: Optional[List[str]] = None,
        title: Optional[str] = None,
        max_tokens: int = 1000
    ) -> Dict[str, Any]:
        """
        Generate a narrative script for an anime opening.
        
        Args:
            num_characters: Number of main characters to feature
            theme: Style of anime (action, romance, fantasy, scifi, comedy)
            character_descriptions: Optional descriptions for each character
            title: Optional title for the anime
            max_tokens: Maximum tokens for the response
            
        Returns:
            Dict containing the narrative and scene descriptions
        """
        # Theme-specific descriptions
        theme_descriptions = {
            "action": "epic battle scenes with powerful poses and dramatic confrontations",
            "romance": "emotional moments with cherry blossoms and nostalgic scenery",
            "fantasy": "magical environments with mystical creatures and spell casting",
            "scifi": "futuristic cityscapes with neon lights and advanced technology",
            "comedy": "exaggerated expressions and funny slice-of-life situations"
        }
        
        theme_desc = theme_descriptions.get(theme, theme_descriptions["action"])
        anime_title = title or f"Untitled {theme.capitalize()} Anime"
        
        # Construct character info section
        character_info = ""
        if character_descriptions and len(character_descriptions) > 0:
            for i, desc in enumerate(character_descriptions):
                character_info += f"Character {i+1}: {desc}\n"
        else:
            # Default to generic character descriptions
            character_info = f"Include {num_characters} unique anime characters with distinct personalities and appearances."
        
        prompt = f"""Create a detailed narrative script for an anime opening titled "{anime_title}".
        
The opening should be in the style of {theme} anime featuring {theme_desc}.

{character_info}

Please structure your response in JSON format with the following sections:
1. "title": The anime title
2. "theme": The anime theme/genre
3. "setting": A brief description of the world/setting
4. "characters": An array of character descriptions, each with "name", "appearance", and "pose" fields
5. "scenes": An array of scene descriptions (5-7 scenes) for the opening sequence, each with:
   - "description": What happens in the scene
   - "visuals": Special visual effects or techniques
   - "timing": Approximate timing in the opening (e.g. "0:05-0:10")
6. "climax": The final dramatic moment of the opening
7. "musical_mood": Description of the music style and mood that would fit this opening

Make it dramatic, visually interesting, and fitting for a {theme} anime opening sequence.
Ensure each character gets a memorable moment in the opening.
"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4-1106-preview",
                messages=[
                    {"role": "system", "content": "You are an expert anime screenwriter specializing in creating iconic opening sequences."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            narrative_json = json.loads(response.choices[0].message.content)
            return narrative_json
        
        except Exception as e:
            print(f"Error generating narrative: {str(e)}")
            # Fallback to a basic structure
            return {
                "title": anime_title,
                "theme": theme,
                "setting": f"A world where {theme} adventures happen.",
                "characters": [{"name": f"Character {i+1}", "appearance": "Distinctive anime style", "pose": "Dramatic pose"} for i in range(num_characters)],
                "scenes": [
                    {
                        "description": "Opening shot of the main setting",
                        "visuals": "Wide angle, panning shot",
                        "timing": "0:00-0:05"
                    },
                    {
                        "description": "Character introductions",
                        "visuals": "Character close-ups with name overlays",
                        "timing": "0:05-0:15"
                    },
                    {
                        "description": "Action sequence showcasing abilities",
                        "visuals": "Fast cuts, dynamic camera movement",
                        "timing": "0:15-0:25"
                    },
                    {
                        "description": "Emotional moment between characters",
                        "visuals": "Slow motion, soft focus",
                        "timing": "0:25-0:35"
                    },
                    {
                        "description": "Final group shot",
                        "visuals": "Freeze frame with title overlay",
                        "timing": "0:35-0:40"
                    }
                ],
                "climax": "All characters posing together as the title appears",
                "musical_mood": f"Energetic {theme} anime theme with vocals"
            }
    
    async def generate_scene_descriptions(
        self,
        narrative: Dict[str, Any],
        num_scenes: int = 8,
        detailed: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Generate more detailed scene descriptions based on the narrative.
        
        Args:
            narrative: The base narrative structure
            num_scenes: Number of scenes to generate
            detailed: Whether to generate detailed descriptions
            
        Returns:
            List of detailed scene descriptions
        """
        base_scenes = narrative.get("scenes", [])
        if len(base_scenes) >= num_scenes or not detailed:
            return base_scenes
        
        try:
            # Extract key information from the narrative
            title = narrative.get("title", "Anime Opening")
            theme = narrative.get("theme", "action")
            characters = narrative.get("characters", [])
            setting = narrative.get("setting", "")
            climax = narrative.get("climax", "")
            
            character_info = "\n".join([
                f"- {char.get('name', 'Character')}: {char.get('appearance', '')}. Signature pose: {char.get('pose', '')}"
                for char in characters
            ])
            
            prompt = f"""Based on the anime opening concept for "{title}" with {theme} theme, create {num_scenes} detailed storyboard scene descriptions.

Setting: {setting}

Characters:
{character_info}

Climax: {climax}

For each scene, include:
1. Detailed visual description
2. Camera movements and angles
3. Character actions and expressions
4. Special effects and animation style
5. Timing in the opening sequence
6. Transition to the next scene

Make each scene visually distinct and create a cohesive flow from beginning to end,
showcasing each character and building up to the climax.
Format as JSON array of scene objects.
"""
            
            response = self.client.chat.completions.create(
                model="gpt-4-1106-preview",
                messages=[
                    {"role": "system", "content": "You are an expert anime storyboard artist."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            scenes_data = json.loads(response.choices[0].message.content)
            if isinstance(scenes_data, dict) and "scenes" in scenes_data:
                return scenes_data["scenes"]
            elif isinstance(scenes_data, list):
                return scenes_data
            else:
                # Fallback to original scenes
                return base_scenes
            
        except Exception as e:
            print(f"Error generating detailed scenes: {str(e)}")
            return base_scenes
    
    async def generate_title_sequence(
        self, 
        title: str,
        theme: str
    ) -> Dict[str, Any]:
        """
        Generate a title sequence design.
        
        Args:
            title: Anime title
            theme: Style theme
            
        Returns:
            Dict with title sequence design details
        """
        try:
            prompt = f"""Design a title sequence for an anime called "{title}" with a {theme} theme.
            
Please provide:
1. Font style description
2. Color scheme
3. Animation effect for the title
4. Background elements
5. Sound effect suggestion
            
Format the response as a JSON object.
"""
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert anime title designer."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            print(f"Error generating title sequence: {str(e)}")
            # Fallback
            return {
                "font_style": "Bold, angular font typical for anime titles",
                "color_scheme": f"Colors fitting {theme} theme",
                "animation_effect": "Fade in with a glow effect",
                "background_elements": "Abstract shapes and light rays",
                "sound_effect": "Dramatic whoosh with a bass drop"
            }
    
    async def generate_character_moments(
        self,
        characters: List[Dict[str, Any]],
        theme: str
    ) -> List[Dict[str, Any]]:
        """
        Generate character-specific moments for each character.
        
        Args:
            characters: List of character descriptions
            theme: Style theme
            
        Returns:
            List of character moments
        """
        if not characters:
            return []
        
        try:
            character_info = "\n".join([
                f"- {char.get('name', 'Character')}: {char.get('appearance', '')}. Signature pose: {char.get('pose', '')}"
                for char in characters
            ])
            
            prompt = f"""For each character in a {theme} anime opening, create a signature moment that highlights their personality and abilities.

Characters:
{character_info}

For each character, describe:
1. The setting/background for their moment
2. Their action or pose
3. Special effects that emphasize their character
4. Camera angle and movement
5. Transition to/from their moment

Format as a JSON array of character moment objects.
"""
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert anime character designer and animator."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            moments_data = json.loads(response.choices[0].message.content)
            if isinstance(moments_data, dict) and "moments" in moments_data:
                return moments_data["moments"]
            elif isinstance(moments_data, list):
                return moments_data
            else:
                # Generate simple moments as fallback
                return [{"character": char.get("name", "Character"), 
                         "moment": f"Dramatic reveal with signature {char.get('pose', 'pose')}"} 
                        for char in characters]
            
        except Exception as e:
            print(f"Error generating character moments: {str(e)}")
            # Fallback
            return [{"character": char.get("name", "Character"), 
                     "moment": f"Dramatic reveal with signature {char.get('pose', 'pose')}"} 
                    for char in characters]

# Example usage
async def main():
    generator = AnimeNarrativeGenerator()
    
    # Generate basic narrative
    narrative = await generator.generate_opening_narrative(
        num_characters=3,
        theme="action",
        title="Cosmic Legends"
    )
    print("Generated Narrative:")
    print(json.dumps(narrative, indent=2))
    
    # Generate detailed scenes
    scenes = await generator.generate_scene_descriptions(narrative)
    print("\nDetailed Scenes:")
    print(json.dumps(scenes, indent=2))
    
    # Generate title sequence
    title_sequence = await generator.generate_title_sequence(
        title=narrative.get("title", "Anime Opening"),
        theme=narrative.get("theme", "action")
    )
    print("\nTitle Sequence Design:")
    print(json.dumps(title_sequence, indent=2))
    
    # Generate character moments
    character_moments = await generator.generate_character_moments(
        characters=narrative.get("characters", []),
        theme=narrative.get("theme", "action")
    )
    print("\nCharacter Moments:")
    print(json.dumps(character_moments, indent=2))

if __name__ == "__main__":
    asyncio.run(main())