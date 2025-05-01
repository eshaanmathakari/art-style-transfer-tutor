# AI Art Style Transfer Tutor 🖼️

[![Python Version](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![YouTube Demo Video](https://img.youtube.com/vi/3oEp5X8jeyE/hqdefault.jpg)](https://youtu.be/3oEp5X8jeyE)

**Transform your photos into famous art styles and learn about the techniques with an interactive AI tutor!**

This project combines the power of OpenAI's DALL-E 3 for image generation and GPT-4o for vision analysis and conversational tutoring to create an educational and creative AI art studio. Upload an image, choose an artist or style, and watch your photo get reimagined while learning *why* it looks that way.


---

## ✨ Features

*   **Image Upload:** Upload your own photos (JPG, PNG, JPEG).
*   **Diverse Art Styles:** Select from a curated list of famous art styles and artists (e.g., Van Gogh, Monet, Ukiyo-e, Pop Art, Pixel Art, and more).
*   **AI-Powered Style Transfer:** Leverages OpenAI DALL-E 3, guided by GPT-4o's analysis of your input image, to generate a stylized version.
*   **Intelligent Prompting:**
    *   Uses GPT-4o Vision to analyze the content of your uploaded image.
    *   Combines this analysis with detailed style descriptions for effective DALL-E 3 prompting.
    *   Supports negative prompting to exclude unwanted elements.
*   **Interactive AI Tutor:**
    *   Provides an initial explanation of the selected art style's key characteristics.
    *   Analyzes the *specifically generated* image using GPT-4o Vision to point out how the style was applied.
    *   Engage in a follow-up chat to ask more questions about the art style.
*   **Customizable Generation:** Control DALL-E 3 parameters like image size, quality (standard/hd), and style (vivid/natural).
*   **Download Results:** Save your generated masterpiece.
*   **Web Interface:** Built with Streamlit for an easy-to-use web application.

---

## 🚀 How It Works

This application orchestrates several AI steps:

1.  **Upload:** The user uploads an image via the Streamlit interface.
2.  **Analyze Content:** The uploaded image is sent to **OpenAI GPT-4o Vision** to generate a detailed textual description of its content, composition, and colors.
3.  **Select Style & Parameters:** The user chooses a target art style and generation parameters (size, quality, negative prompt, etc.).
4.  **Combine Prompts:** The generated image description is combined with the specific characteristics of the chosen style (from `styles.py`) and any negative prompts into a comprehensive prompt for DALL-E.
5.  **Generate Image:** The combined prompt and parameters are sent to the **OpenAI DALL-E 3 API** to generate the stylized image.
6.  **Analyze Generated Image:** The newly created stylized image is sent *back* to **OpenAI GPT-4o Vision** along with information about the target style.
7.  **Explain & Tutor:**
    *   An initial explanation of the style is generated using **OpenAI GPT-4o Mini**.
    *   A second explanation is generated, based on the vision analysis of the *output* image, highlighting specific visual elements that reflect the chosen style.
    *   The user can ask follow-up questions, which are answered contextually by **GPT-4o Mini** using the chat history.
8.  **Display:** The original image, stylized image, download button, and interactive tutor chat are displayed in the Streamlit app.

---

## 📸 Screenshots

![Screenshot of App Interface]([images/screenshot1.png])
*Caption: Main interface showing upload and style selection.*

![Screenshot of Generated Image and Tutor]([images/screenshot1.png])
*Caption: Displaying the original, stylized image, and the AI tutor's analysis.*

---

## 🛠️ Tech Stack

*   **Language:** Python 3.9+
*   **Frontend:** Streamlit
*   **AI Models:**
    *   OpenAI DALL-E 3 (Image Generation)
    *   OpenAI GPT-4o (Image Analysis / Vision)
    *   OpenAI GPT-4o / GPT-4o Mini (Tutoring / Text Generation)
*   **Core Libraries:** `openai`, `Pillow`, `python-dotenv`, `streamlit`

---

## ⚙️ Setup and Installation

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/eshaanmathakari/art-style-transfer-tutor]
    cd art-style-transfer-tutor
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    # Using venv (recommended)
    python -m venv .venv
    # On Windows
    # .venv\Scripts\activate
    # On macOS/Linux
    source .venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up API Key:**
    *   Create a `.env` file in the project root directory. You can copy the example:
        ```bash
        cp .env.example .env
        ```
        *(You should create a `.env.example` file - see below)*
    *   Open the `.env` file and add your OpenAI API key:
        ```dotenv
        OPENAI_API_KEY="your_openai_api_key_here"
        ```
        *Make sure your API key has access to DALL-E 3 and GPT-4o models and sufficient credits.*

---

## ▶️ Usage

Once the setup is complete, run the Streamlit application:

```bash
streamlit run app.py
```

Open your web browser to the local URL provided by Streamlit (usually `http://localhost:8501`).

---

## 🔧 Configuration

*   **API Key:** The application requires an OpenAI API key stored in a `.env` file in the project root.
*   **Styles:** Art styles, their descriptive prompts for DALL-E, and tags for the tutor are defined in `styles.py`. You can easily add or modify styles there.

---

## 💡 Future Improvements

*   Allow users to upload their *own* style reference image.
*   Implement an image comparison slider (original vs. stylized).
*   Add more granular control over style blending/strength (if future APIs allow).
*   Option to save chat history.
*   Deploy as a more permanent web service.

---

## 📄 License

This project is licensed under the MIT License.

---

## 🙏 Acknowledgements

*   OpenAI for their powerful API.
*   The Streamlit team for the easy-to-use web framework.

---
