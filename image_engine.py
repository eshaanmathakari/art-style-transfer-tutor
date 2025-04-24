# image_engine.py
import os
import base64
from io import BytesIO
from PIL import Image
from dotenv import load_dotenv
import streamlit as st # For user feedback (errors/warnings)
from openai import OpenAI, OpenAIError # Import OpenAI client and specific error

load_dotenv() # Load environment variables

# --- Configuration for OpenAI DALL-E ---
# See options: https://platform.openai.com/docs/api-reference/images/create
DALLE_MODEL = "dall-e-3" # Use DALL-E 3 for higher quality
IMAGE_SIZE = "1024x1024" # DALL-E 3 supports 1024x1024, 1792x1024, 1024x1792
IMAGE_QUALITY = "standard" # Options: "standard" or "hd" ("hd" is slower/more costly)
IMAGE_STYLE = "vivid" # Options: "vivid" (hyper-real/dramatic) or "natural" (less hyper-real)

class StyleEngine:
    def __init__(self):
        """Initializes the OpenAI client."""
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            st.error("Error: OPENAI_API_KEY environment variable not set.")
            raise ValueError("OPENAI_API_KEY not found in environment variables.")

        try:
            self.client = OpenAI(api_key=self.api_key)
            print("✅ OpenAI client initialized successfully.")
        except Exception as e:
            st.error(f"Error initializing OpenAI client: {e}")
            print(f"OpenAI Client Initialization failed: {e}")
            raise # Re-raise the exception to stop app execution if client fails

    def _generate_image_openai(self, prompt: str) -> Image.Image | None:
        """Generates an image using the OpenAI DALL-E API."""
        if not self.client:
            st.error("OpenAI client is not initialized.")
            return None

        print(f"➡️ Sending request to OpenAI DALL-E 3 with prompt: '{prompt[:100]}...'") # Log prompt start

        try:
            response = self.client.images.generate(
                model=DALLE_MODEL,
                prompt=prompt,
                n=1,                    # Generate a single image
                size=IMAGE_SIZE,
                quality=IMAGE_QUALITY,
                style=IMAGE_STYLE,
                response_format="b64_json" # Request base64 encoded image data
            )
            print("⬅️ Received response from OpenAI DALL-E 3")

            # --- Process the Response ---
            if response.data and response.data[0].b64_json:
                b64_data = response.data[0].b64_json
                try:
                    image_bytes = base64.b64decode(b64_data)
                    generated_image = Image.open(BytesIO(image_bytes))
                    print("✅ Image successfully generated and decoded from base64.")
                    return generated_image
                except (base64.binascii.Error, IOError) as decode_err:
                    st.error(f"Error decoding base64 image data: {decode_err}")
                    print(f"Base64 decoding error: {decode_err}")
                    return None
            else:
                # Log the response structure if it's unexpected
                st.error("OpenAI API returned an unexpected response format (no b64_json data).")
                print(f"Unexpected OpenAI response structure: {response}")
                return None

        except OpenAIError as e:
            # Handle specific OpenAI API errors (rate limits, invalid requests, etc.)
            error_message = f"OpenAI API Error: {e.type} - {e.message} (Status code: {e.status_code})"
            st.error(error_message)
            print(error_message)
            # You could add specific handling based on e.code (e.g., 'rate_limit_exceeded')
            return None
        except Exception as e:
            # Handle other potential errors (network issues, etc.)
            st.error(f"An unexpected error occurred during image generation: {e}")
            print(f"Unexpected error during OpenAI call: {e}")
            return None

    def apply_style(self, content_img: Image.Image, style_cfg: dict) -> Image.Image | None:
        """
        Applies style using OpenAI DALL-E (Text-to-Image approach).
        The content_img is currently unused by DALL-E text-to-image but kept for potential future use.
        """
        style_name = style_cfg.get('style_name', 'the selected style')
        # Construct a clear prompt for DALL-E 3
        # It's often good to explicitly state the desired transformation
        base_prompt = f"A photo transformed into the style of {style_name}. "
        style_details = style_cfg.get("prompt", f"Artwork in the style of {style_name}.")

        # Combine prompts - DALL-E 3 handles long prompts well.
        # Remove redundant parts if the style_details already mentions the style.
        if f"style of {style_name.lower()}" in style_details.lower():
             full_prompt = style_details # Use the detailed prompt if it already includes the style name
        else:
             full_prompt = base_prompt + style_details

        # Optional: Add guidance for incorporating content (though DALL-E does this implicitly)
        # You could try adding "The scene should retain the main subjects and composition of the original photo."
        # full_prompt += " The scene should retain the main subjects and composition of an original photo provided as context."

        # Limit prompt length if necessary (DALL-E 3 limit is high, but good practice)
        max_prompt_length = 4000 # Check current DALL-E 3 limits if needed
        full_prompt = full_prompt[:max_prompt_length]

        generated_image = self._generate_image_openai(full_prompt)

        if generated_image:
            return generated_image
        else:
            st.warning(f"Failed to generate image for style: {style_name}")
            return None # Return None on failure