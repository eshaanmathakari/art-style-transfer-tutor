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
VISION_MODEL = "gpt-4o"

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
        # --- (Keep this function exactly as it is in your current code) ---
        if not self.client:
            st.error("OpenAI client is not initialized.")
            return None

        print("➡️ Analyzing image content with GPT-4o...")
        try:
            # Convert PIL Image to base64 string
            buffered = BytesIO()
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
                                "text": "Provide a detailed, objective description of this image suitable for an image generation model. Focus on: 1. Main subject(s) and their appearance/pose. 2. Background elements and setting. 3. Overall composition and layout (e.g., wide shot, close-up). 4. Key objects and their spatial relationships. 5. Dominant colors and lighting style. Avoid interpreting meaning or emotion."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/{image_format.lower()};base64,{img_base64}",
                                    "detail": "high"
                                },
                            },
                        ],
                    }
                ],
                max_tokens=300
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

    def _generate_image_openai(self,
                               prompt: str,
                               size: str = "1024x1024",
                               quality: str = "standard",
                               dalle_style: str = "vivid" # 'vivid' or 'natural'
                               ) -> Image.Image | None:
        """Generates an image using the OpenAI DALL-E API based on the combined prompt."""
        if not self.client:
            st.error("OpenAI client is not initialized.")
            return None

        # Use the specific DALL-E model passed or default
        dalle_model_to_use = "dall-e-3" # Hardcoding DALL-E 3 for now

        print(f"➡️ Sending request to OpenAI {dalle_model_to_use}...")
        print(f"   Prompt (start): '{prompt[:150]}...'")
        print(f"   Size: {size}, Quality: {quality}, Style: {dalle_style}")

        try:
            response = self.client.images.generate(
                model=dalle_model_to_use,
                prompt=prompt, # Use the combined prompt
                n=1,
                size=size,        # Use parameter
                quality=quality,  # Use parameter
                style=dalle_style,# Use parameter
                response_format="b64_json"
            )
            print(f"⬅️ Received response from OpenAI {dalle_model_to_use}")

            # --- (Keep the response processing logic exactly as it is) ---
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
            # Add specific check for content policy violation
            if "content_policy_violation" in str(e):
                 st.error("The request was rejected due to OpenAI's content policy. Please modify the prompt or image.")
            return None
        except Exception as e:
            st.error(f"An unexpected error occurred during image generation: {e}")
            print(f"Unexpected error during DALL-E call: {e}")
            return None

    def apply_style(self,
                    content_img: Image.Image,
                    style_cfg: dict,
                    negative_prompt: str = "",
                    size: str = "1024x1024",
                    quality: str = "standard",
                    dalle_style: str = "vivid"
                   ) -> tuple[Image.Image | None, str | None]: # Return image and description
        """
        Applies style by:
        1. Getting description of content_img.
        2. Combining description, style prompt, and negative prompt.
        3. Generating image using DALL-E with specified parameters.
        Returns the generated image and the description used.
        """
        style_name = style_cfg.get('style_name', 'the selected style')
        # Make sure the style prompt focuses *only* on style elements
        style_details_prompt = style_cfg.get("prompt", f"in the style of {style_name}.")

        # --- Step 1: Get Image Description ---
        image_description = None # Initialize
        # Add spinner in app.py, not here
        image_description = self._get_image_description(content_img)

        if not image_description:
            st.error("Could not get a description of the uploaded image. Cannot proceed.")
            return None, None # Return None for both image and description

        # --- Step 2: Combine Prompts (Clearer Structure) ---
        combined_prompt = (
            f"{image_description}. "
            f"Now, recreate this entire scene faithfully but render it completely in the artistic style of {style_name}. "
            f"The style is characterized by: {style_details_prompt}."
        )

        # Add negative prompt if provided
        if negative_prompt and negative_prompt.strip():
            combined_prompt += f" Avoid incorporating the following elements: {negative_prompt.strip()}."

        max_prompt_length = 4000 # DALL-E 3 limit
        combined_prompt = combined_prompt[:max_prompt_length]

        # --- Step 3: Generate Image ---
        generated_image = self._generate_image_openai(
            prompt=combined_prompt,
            size=size,
            quality=quality,
            dalle_style=dalle_style
        )

        if generated_image:
            # Return both the image and the description used to generate it
            return generated_image, image_description
        else:
            st.warning(f"Failed to generate image for style: {style_name}")
            return None, image_description # Return None for image, but still return the description