import os
import openai
import streamlit as st
from dotenv import load_dotenv
from report_translator import translate_text

load_dotenv()

# Use the Meta Llama 3.2 11B Instruct model (Vision version works for text too)
MODEL_NAME ="meta-llama/llama-3.2-11b-vision-instruct"

def get_openai_client():
    """Get OpenAI client with proper API key handling"""
    
    api_key = st.secrets["OPENROUTER_API_KEY"]
    
    return openai.OpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1"
    )

def chat_with_bot(messages, target_lang=None):
    try:
        client = get_openai_client()
        # Prepend system message to restrict to medical questions
        system_message = {
            "role": "system",
            "content": "You are a medical assistant chatbot. Only answer questions related to medicine, health, or medical topics. If the query is not related to medicine, politely decline to answer and suggest asking a medical question."
        }
        messages = [system_message] + messages
        # Send message to OpenRouter (chat format)
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=0.7,
            max_tokens=512
        )

        reply = response.choices[0].message.content.strip()

        # Optional translation
        translated_reply = None
        if target_lang:
            translated_reply = translate_text(reply, target_lang)

        return reply, translated_reply

    except Exception as e:
        return f"❌ Error: {str(e)}", None



from dotenv import load_dotenv
load_dotenv()
