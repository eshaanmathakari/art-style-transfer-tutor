# tutor.py
import os
import base64
from io import BytesIO
from PIL import Image
from openai import OpenAI, OpenAIError
from dotenv import load_dotenv

load_dotenv()

# --- OpenAI Client Initialization (Keep as is) ---
try:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    if not client.api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set or empty.")
except Exception as e:
    print(f"Error initializing OpenAI client: {e}")
    client = None

# --- Constants ---
VISION_MODEL = "gpt-4o" # Or "gpt-4-turbo" if preferred
TEXT_MODEL = "gpt-4o-mini" # Keep tutor responses concise and cheaper

SYSTEM_PROMPT_INITIAL = (
  "You are a knowledgeable and concise art historian and painting instructor. "
  "Explain the key techniques of the requested art style clearly. "
  "Then, specifically mention 2-3 visual characteristics the user is likely to see "
  "in their photo transformed into this style. Keep the total explanation under 120 words."
)

SYSTEM_PROMPT_GENERATED_ANALYSIS = (
    "You are an art historian analyzing an AI-generated image. "
    "The image provided was generated attempting to capture the style of {style_name}. "
    "Briefly (2-3 points, max 100 words) point out specific visual elements *in this image* that reflect the key characteristics of the {style_name} style, such as {style_tags_string}. "
    "Be specific about *what* you see in the image provided."
)

SYSTEM_PROMPT_FOLLOW_UP = (
    "You are a helpful and concise art tutor. Continue the conversation about the art style previously discussed. "
    "Answer the user's latest question based on the chat history provided. Keep answers brief and relevant."
)

# --- Original Explanation Function (Keep as is) ---
def explain(style_name: str, style_cfg: dict) -> str:
    """Generates the initial explanation of the art style."""
    if not client:
         return "Error: OpenAI client could not be initialized."

    tags = style_cfg.get("explain_tags", [])
    tags_string = ", ".join(tags) if tags else "its defining characteristics"
    user_prompt = (
        f"Explain the signature techniques of the {style_name.replace('_', ' ')} art style. "
        f"Then, describe how a typical photograph might change when rendered in this style, "
        f"highlighting elements like {tags_string}. Focus on visual changes."
    )
    try:
        resp = client.chat.completions.create(
            model=TEXT_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_INITIAL},
                {"role": "user",   "content": user_prompt}
            ],
            temperature=0.6,
            max_tokens=150,
        )
        return resp.choices[0].message.content.strip()
    except OpenAIError as e:
        print(f"OpenAI API call failed (initial explain): {e}")
        return f"Error explaining style: {e.message} ({e.status_code})"
    except Exception as e:
        print(f"An unexpected error occurred during initial explanation: {e}")
        return "Error explaining style: An unexpected error occurred."

# --- NEW: Function to Explain the Generated Image ---
def explain_generated_image(generated_image: Image.Image, style_cfg: dict) -> str:
    """Analyzes the *generated* image and explains how the style is visible."""
    if not client:
        return "Error: OpenAI client could not be initialized."
    if not generated_image:
        return "Error: No generated image provided for analysis."

    style_name = style_cfg.get('style_name', 'the selected style')
    tags = style_cfg.get("explain_tags", [])
    tags_string = ", ".join(tags) if tags else "its defining characteristics"

    print(f"➡️ Analyzing generated image for {style_name} style...")
    try:
        # Convert PIL Image to base64
        buffered = BytesIO()
        image_format = generated_image.format if generated_image.format in ["JPEG", "PNG"] else "PNG"
        generated_image.save(buffered, format=image_format)
        img_bytes = buffered.getvalue()
        img_base64 = base64.b64encode(img_bytes).decode('utf-8')

        system_message = SYSTEM_PROMPT_GENERATED_ANALYSIS.format(
            style_name=style_name,
            style_tags_string=tags_string
        )

        response = client.chat.completions.create(
            model=VISION_MODEL, # Use vision model here
            messages=[
                {
                    "role": "system", "content": system_message
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Analyze the provided image based on the system instructions."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/{image_format.lower()};base64,{img_base64}",
                                "detail": "low" # Low detail might be sufficient and faster/cheaper
                            },
                        },
                    ],
                 }
            ],
            max_tokens=150 # Keep analysis concise
        )
        analysis = response.choices[0].message.content.strip()
        print("✅ Generated image analysis received.")
        return analysis

    except OpenAIError as e:
        print(f"OpenAI API call failed (generated analysis): {e}")
        return f"Error analyzing generated image: {e.message} ({e.status_code})"
    except Exception as e:
        print(f"An unexpected error occurred during generated image analysis: {e}")
        return "Error analyzing generated image: An unexpected error occurred."


# --- NEW: Function to Answer Follow-up Questions ---
def answer_follow_up(chat_history: list, style_name: str) -> str:
    """Answers a follow-up question based on the chat history."""
    if not client:
        return "Error: OpenAI client could not be initialized."
    if not chat_history:
        return "Error: No chat history provided."

    print("➡️ Generating follow-up answer...")
    try:
        # The chat history already includes the user's latest question
        messages_for_api = [{"role": "system", "content": SYSTEM_PROMPT_FOLLOW_UP}] + chat_history

        resp = client.chat.completions.create(
            model=TEXT_MODEL, # Use text model for chat
            messages=messages_for_api,
            temperature=0.7,
            max_tokens=150,
        )
        answer = resp.choices[0].message.content.strip()
        print("✅ Follow-up answer generated.")
        return answer
    except OpenAIError as e:
        print(f"OpenAI API call failed (follow-up): {e}")
        return f"Error generating follow-up: {e.message} ({e.status_code})"
    except Exception as e:
        print(f"An unexpected error occurred during follow-up: {e}")
        return "Error generating follow-up: An unexpected error occurred."