from PIL import Image
import openai
import base64
from deep_translator import GoogleTranslator
import os
import streamlit as st
from dotenv import load_dotenv
import pdfplumber
import io

load_dotenv()

def get_openai_client():
    """Get OpenAI client with proper API key handling"""
    try:
        api_key = st.secrets["OPENROUTER_Report_API_KEY"]
    except KeyError:
        api_key = os.getenv("OPENROUTER_Report_API_KEY")

    return openai.OpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1"
    )

def get_vision_client():
    """Get OpenAI client for vision models with separate API key"""
    try:
        api_key = st.secrets["OPENROUTER_API_KEY_VISION"]
    except KeyError:
        api_key = os.getenv("OPENROUTER_API_KEY_VISION")

    return openai.OpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1"
    )

# Use OpenRouter supported models - GPT-4o for vision, Gemini for translation
MODEL_NAME = "google/gemini-2.0-flash-exp:free"
VISION_MODEL = "meta-llama/llama-4-scout:free"

# 🔍 Function to extract text from an image or PDF using LLM vision or pdfplumber
def extract_text(file_path):
    file_extension = os.path.splitext(file_path)[1].lower()

    if file_extension == '.pdf':
        # Extract text from PDF
        try:
            with pdfplumber.open(file_path) as pdf:
                text = ""
                for page in pdf.pages:
                    text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            return f"Error extracting text from PDF: {str(e)}"
    else:
        # Assume it's an image
        try:
            # Encode image to base64 in memory
            image = Image.open(file_path)
            # Convert to RGB if image has alpha channel (RGBA)
            if image.mode == 'RGBA':
                image = image.convert('RGB')
            buffer = io.BytesIO()
            image.save(buffer, format="JPEG")
            base64_image = base64.b64encode(buffer.getvalue()).decode('utf-8')

            prompt = "Extract all the text from this medical report image. Provide only the extracted text without any additional comments or formatting."

            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]
                }
            ]

            client = get_vision_client()

            # Add retry logic for rate limits
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = client.chat.completions.create(
                        model=VISION_MODEL,
                        messages=messages,
                        temperature=0.1,
                        max_tokens=1024
                    )
                    extracted_text = response.choices[0].message.content.strip()
                    return extracted_text
                except Exception as api_error:
                    error_str = str(api_error).lower()
                    if "429" in error_str or "rate" in error_str:
                        if attempt < max_retries - 1:
                            import time
                            time.sleep(2 ** attempt)  # Exponential backoff
                            continue
                        else:
                            return f"Error: Rate limit exceeded for free model. Please try again in a few minutes, or consider upgrading to a paid plan for higher limits."
                    else:
                        # Re-raise non-rate-limit errors
                        raise api_error
        except Exception as e:
            # No fallback available - Tesseract removed for deployment compatibility
            return f"Error: Could not extract text from image. LLM vision failed: {str(e)}. Please try a different image or ensure the image contains clear text."

# 🌐 Function to simplify and translate text to a specified language using LLM for simplification and GoogleTranslator for translation
def translate_text(text, dest_lang="hi", dest_lang_name="Hindi"):
    try:
        # First, simplify the medical report in simple words using LLM
        simplify_prompt = f"Simplify the following medical report text into simple, easy-to-understand words. Explain any medical terms in plain language. Provide only the simplified text:\n\n{text}"
        simplify_messages = [{"role": "user", "content": simplify_prompt}]
        client = get_openai_client()
        simplify_response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=simplify_messages,
            temperature=0.5,
            max_tokens=1024
        )
        simplified = simplify_response.choices[0].message.content.strip()

        # Then, translate to the target language using GoogleTranslator for reliability
        if dest_lang != "en":
            translator = GoogleTranslator(source='en', target=dest_lang)
            final_text = translator.translate(simplified)
        else:
            final_text = simplified

        return final_text
    except Exception as e:
        # Fallback: directly translate the original text using GoogleTranslator
        try:
            if dest_lang != "en":
                translator = GoogleTranslator(source='auto', target=dest_lang)
                final_text = translator.translate(text)
            else:
                final_text = text
            return final_text
        except Exception as fallback_e:
            # Last resort: return original text
            return text
