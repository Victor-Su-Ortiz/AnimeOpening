import replicate
import base64
import os
import requests
from PIL import Image
from io import BytesIO
import numpy as np
import uuid
import asyncio
import time

class AnimeImageTransformer:
    """Class to handle anime-style transformations using Replicate models"""
    
    def __init__(self, api_token=None):
        self.api_token = api_token or os.environ.get("REPLICATE_API_TOKEN")
        self.client = replicate.Client(api_token=self.api_token)
        self.output_dir = "transformed_images"
        os.makedirs(self.output_dir, exist_ok=True)
    
    async def transform_image(self, image_path, theme="action", character_role=None):
        """Transform an image to anime style with specific theme considerations"""

        print("we are trying to do this")
        
        # Different models for different themes/styles
        models = {
            "action": "cjwbw/portraitplus:e14bbf14452cf3e2699402a347d38e33d2364636bbed4f3fa9e0b7d44e72b028",
            "romance": "cjwbw/animegan2-pytorch:e4a3f2b729c29a6dc9a36590806b8c8294b0181d47c3c0942be9d8622f3a3960",
            "fantasy": "replicate/white-box-diffusion:e272542c4c98a9d18b8c58d05ead3ab3a2f2ff49fa47897724aae1eb390b0caf",
            "scifi": "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",
            "comedy": "cjwbw/animegan2-pytorch:e4a3f2b729c29a6dc9a36590806b8c8294b0181d47c3c0942be9d8622f3a3960"
        }
        
        # Choose model based on theme
        model_id = models.get(theme, models["action"])
        
        # Different prompts for different themes
        prompts = {
            "action": "anime character in dynamic action pose, battle ready, dramatic lighting",
            "romance": "anime character in slice of life setting, soft lighting, cherry blossoms",
            "fantasy": "anime character with magical elements, fantasy world, mystical environment",
            "scifi": "anime character in futuristic cyberpunk setting, neon lights, high-tech",
            "comedy": "anime character with exaggerated expression, comedic pose, vibrant colors"
        }
        
        # Adjust prompt based on character role if provided
        if character_role:
            base_prompt = prompts.get(theme, prompts["action"])
            prompt = f"{base_prompt}, {character_role} character"
        else:
            prompt = prompts.get(theme, prompts["action"])
        
        try:
            # Read and prepare the image
            with open(image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")
            
            # # Choose model parameters based on the selected model
            # if "sdxl" in model_id:
            #     # For Stable Diffusion models
            #     output = self.client.run(
            #         model_id,
            #         input={
            #             "prompt": prompt,
            #             "image": f"data:image/jpeg;base64,{image_data}",
            #             "strength": 0.7,  # Keep some original features
            #             "num_inference_steps": 30,
            #             "guidance_scale": 7.5,
            #             "negative_prompt": "deformed, distorted, disfigured, poorly drawn, bad anatomy, wrong anatomy, extra limb, missing limb, floating limbs, mutated hands and fingers, disconnected limbs, mutation, mutated, ugly, disgusting, blurry, amputation"
            #         }
            #     )
            #     image_url = output[0]  # The output is a URL to the generated image
            
            # elif "animegan2" in model_id:
            #     # For AnimeGAN models
            #     output = self.client.run(
            #         model_id,
            #         input={
            #             "image": f"data:image/jpeg;base64,{image_data}"
            #         }
            #     )
            #     image_url = output  # The output is a URL to the transformed image
            
            # elif "portraitplus" in model_id:
            #     # For PortraitPlus model
            #     output = self.client.run(
            #         model_id, 
            #         input={
            #             "image": f"data:image/jpeg;base64,{image_data}",
            #             "prompt": prompt,
            #             "negative_prompt": "deformed, distorted, disfigured, poorly drawn, bad anatomy, wrong anatomy, extra limb, missing limb, floating limbs, mutated hands and fingers, disconnected limbs, mutation, mutated, ugly, disgusting, blurry, amputation"
            #         }
            #     )
            #     image_url = output[0]  # The output is a URL to the generated image
            
            # elif "white-box-diffusion" in model_id:
            #     # For White Box Diffusion
            #     output = self.client.run(
            #         model_id,
            #         input={
            #             "image": f"data:image/jpeg;base64,{image_data}",
            #             "prompt": prompt,
            #             "guidance_scale": 7.5,
            #             "num_inference_steps": 50,
            #             "seed": np.random.randint(0, 1000000)
            #         }
            #     )
            #     image_url = output[0]  # The output is a URL to the generated image
            
            # else:
                # Generic approach for other models
                # output = self.client.run(
                #     model_id,
                #     input={
                #         "image": f"data:image/jpeg;base64,{image_data}"
                #     }
                # )
                print("Hello World")
                input = {
                    "prompt": "anime character in dynamic action pose, battle ready, dramatic lighting",
                    "main_face_image":  f"data:image/jpeg;base64,{image_data}"
                }

                output = replicate.run(
                    "bytedance/pulid:43d309c37ab4e62361e5e29b8e9e867fb2dcbcec77ae91206a8d95ac5dd451a0",
                    input=input
                )
                image_url = output
            
            # Download the transformed image
            response = requests.get(image_url[0])
            if response.status_code == 200:
                # Generate a unique filename
                output_filename = f"{self.output_dir}/transformed_{uuid.uuid4()}.png"
                
                # Save the image
                img = Image.open(BytesIO(response.content))
                img.save(output_filename)
                
                return output_filename
            else:
                raise Exception(f"Failed to download transformed image: HTTP {response.status_code}")
        
        except Exception as e:
            print(f"Error transforming image: {str(e)}")
            # Return the original image as fallback
            return image_path
    
    async def batch_transform(self, image_paths, theme="action", character_roles=None):
        """Transform multiple images in parallel"""
        if character_roles and len(character_roles) != len(image_paths):
            # If character_roles don't match images, ignore them
            character_roles = None
        
        tasks = []
        for i, path in enumerate(image_paths):
            role = character_roles[i] if character_roles else None
            tasks.append(self.transform_image(path, theme, role))
        
        return await asyncio.gather(*tasks)
    
    async def apply_anime_effects(self, image_path, effect_type="speed_lines"):
        """Apply anime-specific effects to images"""
        effects = {
            "speed_lines": "nlpconnect/anime-effects:c49e5dc2ed8a8e31f46a1c47a7d14c365b31ea31a7a90a370615f2eed5c1ff57",
            "sparkle": "nlpconnect/anime-effects:c49e5dc2ed8a8e31f46a1c47a7d14c365b31ea31a7a90a370615f2eed5c1ff57",
            "impact_lines": "nlpconnect/anime-effects:c49e5dc2ed8a8e31f46a1c47a7d14c365b31ea31a7a90a370615f2eed5c1ff57",
            "emotional_glow": "nlpconnect/anime-effects:c49e5dc2ed8a8e31f46a1c47a7d14c365b31ea31a7a90a370615f2eed5c1ff57"
        }
        
        # For this hackathon demo, we'll use a single model but with different prompts
        model_id = effects.get(effect_type, effects["speed_lines"])
        
        effect_prompts = {
            "speed_lines": "add anime speed lines effect",
            "sparkle": "add anime sparkle effect and stars",
            "impact_lines": "add anime impact lines effect",
            "emotional_glow": "add anime emotional glow effect"
        }
        
        prompt = effect_prompts.get(effect_type, effect_prompts["speed_lines"])
        
        try:
            with open(image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")
            
            output = self.client.run(
                model_id,
                input={
                    "image": f"data:image/jpeg;base64,{image_data}",
                    "prompt": prompt
                }
            )
            
            # Download and save the effected image
            response = requests.get(output[0])
            if response.status_code == 200:
                output_filename = f"{self.output_dir}/effect_{uuid.uuid4()}.png"
                img = Image.open(BytesIO(response.content))
                img.save(output_filename)
                return output_filename
            else:
                raise Exception(f"Failed to download effected image: HTTP {response.status_code}")
        
        except Exception as e:
            print(f"Error applying effect: {str(e)}")
            return image_path
    
    async def generate_background(self, theme, prompt_addition=None):
        """Generate anime-style background based on theme"""
        
        background_prompts = {
            "action": "epic anime battle background, dramatic lighting, action scene",
            "romance": "anime slice of life background, cherry blossoms, sunset, school or park scene",
            "fantasy": "fantasy anime world background, magical forest, mystical castle, glowing elements",
            "scifi": "futuristic cyberpunk anime city background, neon lights, high-tech, night scene",
            "comedy": "colorful anime slice of life background, school or home setting, vibrant"
        }
        
        base_prompt = background_prompts.get(theme, background_prompts["action"])
        prompt = f"{base_prompt}, {prompt_addition}" if prompt_addition else base_prompt
        
        try:
            # Use Stable Diffusion for background generation
            model_id = "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b"
            
            output = self.client.run(
                model_id,
                input={
                    "prompt": prompt,
                    "width": 1280,
                    "height": 720,
                    "num_inference_steps": 30,
                    "guidance_scale": 7.5,
                    "negative_prompt": "deformed, distorted, disfigured, poorly drawn, bad anatomy, wrong anatomy, extra limb, missing limb, floating limbs, mutated hands and fingers, disconnected limbs, mutation, mutated, ugly, disgusting, blurry, amputation"
                }
            )
            
            # Download and save the background
            response = requests.get(output[0])
            if response.status_code == 200:
                output_filename = f"{self.output_dir}/bg_{uuid.uuid4()}.png"
                img = Image.open(BytesIO(response.content))
                img.save(output_filename)
                return output_filename
            else:
                raise Exception(f"Failed to download background: HTTP {response.status_code}")
        
        except Exception as e:
            print(f"Error generating background: {str(e)}")
            # Return a default background as fallback
            return "assets/backgrounds/default.jpg"

# Usage example
async def main():
    transformer = AnimeImageTransformer()
    
    # Example: Transform a single image
    transformed = await transformer.transform_image("sample.jpg", theme="action")
    print(f"Transformed image saved to: {transformed}")
    
    # Example: Transform multiple images
    batch_results = await transformer.batch_transform(
        ["sample1.jpg", "sample2.jpg", "sample3.jpg"],
        theme="fantasy",
        character_roles=["protagonist", "sidekick", "villain"]
    )
    print("Batch transformation results:", batch_results)
    
    # Example: Apply anime effect
    effected = await transformer.apply_anime_effects("transformed.jpg", effect_type="speed_lines")
    print(f"Effect applied and saved to: {effected}")
    
    # Example: Generate background
    background = await transformer.generate_background(
        theme="scifi", 
        prompt_addition="Tokyo-inspired cityscape"
    )
    print(f"Background generated and saved to: {background}")

if __name__ == "__main__":
    asyncio.run(main())