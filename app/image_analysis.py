import openai
import base64
import os
import streamlit as st
from dotenv import load_dotenv
from report_translator import translate_text

load_dotenv()

def get_openai_client():
    """Get OpenAI client with proper API key handling"""
    try:
        api_key = st.secrets["OPENROUTER_API_KEY"]
    except KeyError:
        api_key = os.getenv("OPENROUTER_API_KEY")

    return openai.OpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1"
    )

def analyze_medical_image(image_path, image_type, target_lang=None):
    try:
        client = get_openai_client()
        # Encode image to base64
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')

        # Use GPT-4o for vision
        vision_model = "meta-llama/llama-3.2-11b-vision-instruct"

        # Create prompt based on image type
        if image_type == "X-ray":
            prompt = "You are a radiologist analyzing an X-ray image. Identify any fractures, dislocations, or abnormalities in bones and joints. Describe the affected areas precisely, assess severity, and provide medical insights. Note: This is not a diagnosis - consult a healthcare professional."
        elif image_type == "CT Scan":
            prompt = "You are a radiologist analyzing a CT scan image. Identify any abnormalities in organs, tissues, or structures. Describe findings in detail, assess potential conditions, and provide medical insights. Note: This is not a diagnosis - consult a healthcare professional."
        elif image_type == "MRI Scan":
            prompt = "You are a radiologist analyzing an MRI scan image. Identify any abnormalities in soft tissues, brain, spine, or joints. Describe findings in detail, assess potential conditions, and provide medical insights. Note: This is not a diagnosis - consult a healthcare professional."
        elif image_type == "Skin Rash":
            prompt = "You are a dermatologist analyzing a skin condition image. Describe the rash appearance, distribution, and characteristics. Suggest possible causes and provide general treatment recommendations. Note: This is not a diagnosis - consult a healthcare professional."
        else:
            prompt = "Describe this medical image in detail and provide any relevant medical observations."

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }
        ]

        response = client.chat.completions.create(
            model=vision_model,
            messages=messages,
            temperature=0.7,
            max_tokens=512
        )

        reply = response.choices[0].message.content.strip()

        # Optional translation
        if target_lang:
            reply = translate_text(reply, target_lang)

        return reply

    except Exception as e:
        return f"❌ Error analyzing image: {str(e)}"
