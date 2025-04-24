# tutor.py
import os
from openai import OpenAI, OpenAIError # Import specific error type
from dotenv import load_dotenv

load_dotenv() # Load environment variables when this module is imported

# Instantiate the client. It will automatically pick up the API key from the environment variable.
# Consider adding error handling here if the key is missing
try:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    if not client.api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set or empty.")
except Exception as e:
    print(f"Error initializing OpenAI client: {e}")
    client = None # Set client to None if initialization fails

SYSTEM_PROMPT = (
  "You are a knowledgeable and concise art historian and painting instructor. "
  "Explain the key techniques of the requested art style clearly. "
  "Then, specifically mention 2-3 visual characteristics the user is likely to see "
  "in their photo transformed into this style. Keep the total explanation under 120 words."
)

def explain(style_name: str, style_cfg: dict) -> str:
    """Generates an explanation of the art style using an LLM."""
    if not client:
         return "Error: OpenAI client could not be initialized. Check API key and configuration."

    # Use explain_tags for more targeted explanation
    tags = style_cfg.get("explain_tags", [])
    tags_string = ", ".join(tags) if tags else "its defining characteristics"

    user_prompt = (
        f"Explain the signature techniques of the {style_name.replace('_', ' ')} art style. "
        f"Then, describe how a typical photograph might change when rendered in this style, "
        f"highlighting elements like {tags_string}. Focus on visual changes."
    )

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini", # Or another preferred model
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": user_prompt}
            ],
            temperature=0.6, # Slightly lower temp for more focused explanation
            max_tokens=150, # Limit token usage
        )
        return resp.choices[0].message.content.strip()
    except OpenAIError as e:
        print(f"OpenAI API call failed: {e}")
        return f"Error explaining style: Could not connect to the explanation service. ({e.status_code})"
    except Exception as e:
        print(f"An unexpected error occurred during explanation: {e}")
        return "Error explaining style: An unexpected error occurred."