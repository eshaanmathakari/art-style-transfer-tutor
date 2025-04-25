# app.py
import streamlit as st
from PIL import Image
from dotenv import load_dotenv
import io # Needed for image handling if analysis is added

# --- Load .env file BEFORE importing modules that need it ---
load_dotenv()

# --- Now import your other modules ---
from styles import STYLES
# Use the new image engine
from image_engine import StyleEngine
from tutor import explain

@st.cache_resource
def load_style_engine():
    """Loads the image generation engine."""
    print("--- Initializing Style Engine (OpenAI DALL-E) ---") # Updated print statement
    try:
        engine = StyleEngine() # This now initializes the OpenAI client
        print("--- Style Engine Initialized ---")
        return engine
    except Exception as e:
        st.error(f"Fatal Error: Could not initialize the Style Engine: {e}")
        print(f"Style Engine Initialization failed: {e}")
        return None

# --- Streamlit App Code ---
st.set_page_config(page_title="Art Style Transfer Tutor", layout="wide")
st.title("🖼️ Art Style Transfer Tutor")
st.markdown("Upload your photo, choose an art style, and see it transformed! An AI tutor will explain the style.")

# --- Load the engine (will be cached after first run) ---
engine = load_style_engine()

# --- UI Elements ---
uploaded_file = st.file_uploader("1. Upload your photo", type=["jpg", "png", "jpeg"])
style_key = st.selectbox("2. Choose an art style", list(STYLES.keys()), format_func=lambda k: STYLES[k]['style_name'])

# Add a Generate button
generate_button = st.button("3. Generate Stylized Image & Explanation", type="primary", disabled=(not uploaded_file or not style_key or not engine))

st.divider()

# --- Main Logic ---
if generate_button and uploaded_file is not None and style_key and engine:
    col1, col2 = st.columns(2)

    with col1:
        st.header("Original Image")
        try:
            content_img = Image.open(uploaded_file).convert("RGB")
            # Display the uploaded image
            max_width = 512 # Limit display width for consistency
            aspect_ratio = content_img.height / content_img.width
            st.image(content_img, caption="Your Upload", use_container_width =True) # Use column width better
        except Exception as e:
            st.error(f"Error loading image: {e}")
            st.stop() # Stop execution if image loading fails

    # --- Call Image Generation and Explanation ---
    selected_style_config = STYLES[style_key]
    style_name = selected_style_config['style_name']

    with col2:
        st.header(f"Stylized as {style_name}")
        with st.spinner(f"Applying {style_name} style using OpenAI DALL-E 3... (This may take 20-60 seconds)"):
            try:
             # --- Generate Image ---
                stylized_image = engine.apply_style(content_img, selected_style_config)
                if stylized_image:
                    st.image(stylized_image, caption=f"In the style of {style_name}", use_column_width=True)
                else:
                    # Error messages are handled within the engine, show a fallback here
                    st.error("Image generation failed. Please check the logs or try again.")

            except Exception as e:
                st.error(f"An error occurred during style application: {e}")
                print(f"Error in apply_style call: {e}") # Log to console

    # --- Generate Explanation (always attempt this after generation attempt) ---
    st.markdown("--- \n ### 🎨 Art Tutor Explanation") # Use markdown for better formatting
    with st.spinner("Generating explanation..."):
        try:
            explanation_text = explain(style_name, selected_style_config)
            st.info(explanation_text) # Use st.info for styled text box
        except Exception as e:
            st.error(f"Could not generate explanation: {e}")

elif generate_button and not engine:
     st.error("Image generation engine failed to load. Cannot proceed.")

elif not uploaded_file:
    st.info("Please upload an image to get started.")