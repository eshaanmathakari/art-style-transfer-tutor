# image_engine.py
import os
import base64
from io import BytesIO
from PIL import Image
from dotenv import load_dotenv
import streamlit as st
from openai import OpenAI, OpenAIError

load_dotenv()

# --- Configuration for OpenAI ---
VISION_MODEL = "gpt-4o" # Use GPT-4o for combined vision and text capabilities
DALLE_MODEL = "dall-e-3"
IMAGE_SIZE = "1024x1024"
IMAGE_QUALITY = "standard" # or "hd"
IMAGE_STYLE = "vivid" # or "natural"

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
            raise

    def _get_image_description(self, image: Image.Image) -> str | None:
        """Analyzes the image using GPT-4o and returns a detailed description."""
        if not self.client:
            st.error("OpenAI client is not initialized.")
            return None

        print("➡️ Analyzing image content with GPT-4o...")
        try:
            # Convert PIL Image to base64 string
            buffered = BytesIO()
            # Ensure saving in a common format like PNG or JPEG for vision model
            image_format = image.format if image.format in ["JPEG", "PNG"] else "PNG"
            image.save(buffered, format=image_format)
            img_bytes = buffered.getvalue()
            img_base64 = base64.b64encode(img_bytes).decode('utf-8')

            response = self.client.chat.completions.create(
                model=VISION_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                # Prompt for detailed description suitable for re-generation
                                "text": "Provide a detailed, objective description of this image suitable for an image generation model. Focus on: 1. Main subject(s) and their appearance/pose. 2. Background elements and setting. 3. Overall composition and layout (e.g., wide shot, close-up). 4. Key objects and their spatial relationships. 5. Dominant colors and lighting style. Avoid interpreting meaning or emotion."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/{image_format.lower()};base64,{img_base64}",
                                    "detail": "high" # Use high detail for better analysis
                                },
                            },
                        ],
                    }
                ],
                max_tokens=300 # Limit description length
            )
            description = response.choices[0].message.content.strip()
            print(f"✅ Image description received: {description[:100]}...")
            return description

        except OpenAIError as e:
            st.error(f"OpenAI Vision API Error: {e.message} (Status code: {e.status_code})")
            print(f"OpenAI Vision API Error: {e}")
            return None
        except Exception as e:
            st.error(f"An unexpected error occurred during image analysis: {e}")
            print(f"Unexpected error during image analysis: {e}")
            return None

    def _generate_image_openai(self, prompt: str) -> Image.Image | None:
        """Generates an image using the OpenAI DALL-E API based on the combined prompt."""
        if not self.client:
            st.error("OpenAI client is not initialized.")
            return None

        print(f"➡️ Sending request to OpenAI DALL-E 3 with combined prompt: '{prompt[:150]}...'")

        try:
            response = self.client.images.generate(
                model=DALLE_MODEL,
                prompt=prompt, # Use the combined prompt
                n=1,
                size=IMAGE_SIZE,
                quality=IMAGE_QUALITY,
                style=IMAGE_STYLE,
                response_format="b64_json"
            )
            print("⬅️ Received response from OpenAI DALL-E 3")

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
                st.error("OpenAI API returned an unexpected response format (no b64_json data).")
                print(f"Unexpected OpenAI response structure: {response}")
                return None

        except OpenAIError as e:
            error_message = f"OpenAI DALL-E API Error: {e.message} (Status code: {e.status_code})"
            st.error(error_message)
            print(error_message)
            return None
        except Exception as e:
            st.error(f"An unexpected error occurred during image generation: {e}")
            print(f"Unexpected error during DALL-E call: {e}")
            return None

    def apply_style(self, content_img: Image.Image, style_cfg: dict) -> Image.Image | None:
        """
        Applies style by:
        1. Getting a description of the content_img using a vision model.
        2. Combining the description with the target style prompt.
        3. Generating a new image using DALL-E with the combined prompt.
        """
        style_name = style_cfg.get('style_name', 'the selected style')
        style_details_prompt = style_cfg.get("prompt", f"in the style of {style_name}.")

        # --- Step 1: Get Image Description ---
        with st.spinner("Analyzing image content..."): # Add spinner for this step
            image_description = self._get_image_description(content_img)

        if not image_description:
            st.error("Could not get a description of the uploaded image. Cannot proceed with style transfer.")
            return None # Stop if description fails

        # --- Step 2: Combine Prompts ---
        # Construct the final prompt for DALL-E
        # Example structure: "{Detailed Description}. Now render this scene {Style Details Prompt}"
        combined_prompt = f"{image_description}. Now, render this scene {style_details_prompt}"

        # Optional: Refine prompt combination logic if needed based on testing
        # e.g., ensure style isn't mentioned twice redundantly.

        max_prompt_length = 4000 # DALL-E 3 limit
        combined_prompt = combined_prompt[:max_prompt_length]

        # --- Step 3: Generate Image ---
        # The spinner message in app.py will cover this part
        generated_image = self._generate_image_openai(combined_prompt)

        if generated_image:
            return generated_image
        else:
            # Error message is handled within _generate_image_openai
            st.warning(f"Failed to generate image for style: {style_name}")
            return None