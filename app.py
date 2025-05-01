# app.py
import streamlit as st
from PIL import Image
from dotenv import load_dotenv
import io
import base64 # Needed for download button

# --- Load .env file VERY FIRST ---
load_dotenv()
# --- Now import your other modules ---
try:
    from styles import STYLES
    from image_engine import StyleEngine
    # Import all necessary functions from tutor
    from tutor import explain, explain_generated_image, answer_follow_up
except ImportError as e:
    # If imports fail, show error immediately and stop
    st.error(f"Failed to import necessary modules: {e}. Please check tutor.py, image_engine.py, and styles.py for errors.")
    st.stop()
except Exception as e:
    st.error(f"An unexpected error occurred during imports: {e}")
    st.stop()
# --- Streamlit App Code ---
st.set_page_config(page_title="Art Style Transfer Tutor", layout="wide")
st.title("🖼️ Enhanced Art Style Transfer Tutor")
st.markdown("Upload photo, choose style & parameters, get stylized image & AI tutor analysis!")


# --- Initialize session state ---
# Use keys to prevent errors if accessed before assignment
default_keys = {
    "messages": [],
    "generated_img_data": None,
    "generated_img_description": None,
    "current_style_name": None,
    "current_style_key": None,
    "content_img_display": None # To hold the original image for display
}
for key, default_value in default_keys.items():
    if key not in st.session_state:
        st.session_state[key] = default_value


# --- Cache the StyleEngine ---
# This is crucial for performance and avoiding re-initialization
@st.cache_resource
def load_style_engine():
    """Loads the image generation engine. Handles potential errors."""
    print("--- Attempting to initialize Style Engine (OpenAI DALL-E) ---")
    try:
        engine = StyleEngine() # This initializes the OpenAI client
        print("--- Style Engine Initialized Successfully ---")
        return engine
    except ValueError as e: # Catch specific error for missing API key
         st.error(f"Style Engine Initialization Error: {e}. Have you set OPENAI_API_KEY in your .env file?")
         return None
    except Exception as e:
        # Catch any other unexpected errors during initialization
        st.error(f"Fatal Error: Could not initialize the Style Engine: {e}")
        print(f"Style Engine Initialization failed: {e}")
        return None

# --- Load the engine ---
engine = load_style_engine()

# Stop execution if engine failed to load
if not engine:
    st.warning("Image generation engine failed to load. Cannot proceed. Please check API keys and console logs.")
    st.stop()

# --- UI Layout ---
col_input, col_output = st.columns([1, 2]) # Input controls on left (weight 1), output on right (weight 2)

with col_input:
    st.header("🎨 Input & Style Settings")

    # --- File Uploader ---
    uploaded_file = st.file_uploader(
        "1. Upload your photo",
        type=["jpg", "png", "jpeg"],
        key="file_uploader" # Assign a key for stability
    )

    # Process and display uploaded image immediately if available
    if uploaded_file is not None:
        try:
            # Store the loaded image in session state for display in the output column
            st.session_state.content_img_display = Image.open(uploaded_file).convert("RGB")
        except Exception as e:
            st.error(f"Error loading image: {e}")
            st.session_state.content_img_display = None # Clear on error
            uploaded_file = None # Treat as if no file is uploaded if error occurs
    else:
         st.session_state.content_img_display = None # Clear if no file is uploaded


    # --- Style Selection ---
    style_key = st.selectbox(
        "2. Choose an art style",
        list(STYLES.keys()),
        format_func=lambda k: STYLES[k]['style_name'],
        key="style_selector",
        disabled=(uploaded_file is None) # Disable if no image uploaded
    )

    # --- Generation Parameters ---
    st.subheader("⚙️ Generation Parameters")
    dalle_size = st.selectbox(
        "Image Size (Aspect Ratio)",
        ("1024x1024", "1792x1024", "1024x1792"),
        key="dalle_size",
        disabled=(uploaded_file is None)
    )
    dalle_quality = st.radio(
        "Image Quality",
        ("standard", "hd"), horizontal=True, key="dalle_quality",
        disabled=(uploaded_file is None), help="HD takes longer and costs more."
    )
    # Use unique key like 'dalle_style_param' to avoid conflicts
    dalle_style_param = st.radio(
        "DALL-E Style",
        ("vivid", "natural"), horizontal=True, key="dalle_style_param",
        disabled=(uploaded_file is None), help="'Vivid' is hyper-real/dramatic, 'Natural' is less so."
    )
    negative_prompt = st.text_input(
        "Negative Prompt (optional - things to avoid)",
        key="negative_prompt", placeholder="e.g., text, words, blurry, deformed",
        disabled=(uploaded_file is None)
    )

    # --- Generate Button ---
    generate_button = st.button(
        "🚀 Generate Stylized Image & Tutor Analysis",
        type="primary",
        disabled=(uploaded_file is None or not style_key) # Ensure file and style are selected
    )



with col_output:
    st.header("🖼️ Results & Tutor")

    # Define placeholders *before* they might be used conditionally
    generation_placeholder = st.empty()
    tutor_placeholder = st.container()

    # --- Display Original Image ---
    if st.session_state.content_img_display:
        st.subheader("Original Image")
        st.image(st.session_state.content_img_display, caption="Your Upload", use_container_width=True)
        st.markdown("---") # Separator
    elif uploaded_file is None: # Only show if no file is uploaded yet
        st.info("Upload an image and select a style on the left to begin.")

    # --- Generation Logic ---
    # This block runs ONLY when the button is clicked AND prerequisites are met
    if generate_button and st.session_state.content_img_display and style_key:
        # 1. Clear previous results from session state for a fresh run
        st.session_state.messages = []
        st.session_state.generated_img_data = None
        st.session_state.generated_img_description = None
        st.session_state.current_style_name = STYLES[style_key]['style_name']
        st.session_state.current_style_key = style_key # Store key for potential later use

        selected_style_config = STYLES[style_key]
        style_name_display = st.session_state.current_style_name # Use state variable

        st.subheader(f"Stylized as {style_name_display}")


        # Placeholders for dynamic content update
        generation_placeholder = st.empty() # For image + download button
        tutor_placeholder = st.container()  # For all tutor messages and chat input

        stylized_image = None # Initialize before try block

        try:
            # --- Call Image Generation ---
            # Use a single spinner for the multi-step generation process
            with st.spinner(f"Generating ({style_name_display})... Step 1/3: Analyzing input image..."):
                stylized_image, img_description = engine.apply_style(
                    content_img=st.session_state.content_img_display, # Use image from state
                    style_cfg=selected_style_config,
                    negative_prompt=st.session_state.negative_prompt,
                    size=st.session_state.dalle_size,
                    quality=st.session_state.dalle_quality,
                    dalle_style=st.session_state.dalle_style_param # Use unique key here
                )
                st.session_state.generated_img_description = img_description # Save description

            # --- Process if Image Generation Successful ---
            if stylized_image:
                # --- Generate Explanations ---
                with st.spinner(f"Generating ({style_name_display})... Step 2/3: Initial explanation..."):
                    initial_explanation = explain(style_name_display, selected_style_config)
                    st.session_state.messages.append({"role": "assistant", "content": f"**About {style_name_display} Style:**\n{initial_explanation}"})

                with st.spinner(f"Generating ({style_name_display})... Step 3/3: Analyzing generated image..."):
                    generated_analysis = explain_generated_image(stylized_image, selected_style_config)
                    st.session_state.messages.append({"role": "assistant", "content": f"**In Your Generated Image:**\n{generated_analysis}"})

                # --- Display Generated Image and Download ---
                with generation_placeholder.container(): 
                    st.image(stylized_image, caption=f"Generated in the style of {style_name_display}", use_container_width=True)

                    # Prepare image data for download
                    buffered = io.BytesIO()
                    stylized_image.save(buffered, format="PNG")
                    st.session_state.generated_img_data = buffered.getvalue()

                    st.download_button(
                       label="⬇️ Download Stylized Image",
                       data=st.session_state.generated_img_data,
                       file_name=f"stylized_{style_name_display.lower().replace(' ', '_')}.png",
                       mime="image/png",
                       key="download_button"
                    )

                    # Optionally display the description used for generation
                    if img_description:
                        with st.expander("See Image Description Used for Generation"):
                            st.info(img_description)

            # --- Handle Image Generation Failure ---
            else:
                with generation_placeholder.container():
                    st.error("Image generation failed. Please check parameters/logs or try again.")
                st.session_state.messages = [] 

        # --- Catch Errors during the Generation Process ---
        except Exception as e:
            st.error(f"An unexpected error occurred during the generation process: {e}")
            print(f"Error during generation block: {e}") 
            st.session_state.messages = []


    # --- Display Tutor Chat Interface ---
    if st.session_state.messages:
        with tutor_placeholder: 
            st.markdown("--- \n ### 💬 AI Art Tutor Chat")

            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

            if prompt := st.chat_input("Ask a follow-up question about the style...", key="chat_input"):
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)

                with st.chat_message("assistant"):
                    message_placeholder = st.empty()
                    with st.spinner("Thinking..."):
                        current_style_name = st.session_state.get("current_style_name", "the current style")
                        full_response = answer_follow_up(st.session_state.messages, current_style_name)
                        message_placeholder.markdown(full_response)

                st.session_state.messages.append({"role": "assistant", "content": full_response})
