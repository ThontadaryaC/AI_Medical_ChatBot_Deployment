import streamlit.components.v1 as components

def speak_text_component(text):
    """Custom TTS component using browser speech synthesis"""
    if not text or not text.strip():
        return

    # Escape special characters for JavaScript
    escaped_text = text.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')

    html_code = f"""
    <div id="tts-container">
        <button id="tts-button" style="background-color: #4CAF50; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; font-size: 16px;">
            🔊 Speak
        </button>
        <div id="tts-status" style="margin-top: 10px; font-size: 14px;"></div>
    </div>

    <script>
        (function() {{
            const button = document.getElementById('tts-button');
            const statusDiv = document.getElementById('tts-status');
            let isSpeaking = false;

            button.addEventListener('click', function() {{
                if (isSpeaking) {{
                    // Stop current speech
                    if ('speechSynthesis' in window) {{
                        speechSynthesis.cancel();
                    }}
                    isSpeaking = false;
                    button.textContent = '🔊 Speak';
                    statusDiv.textContent = 'Speech stopped';
                    return;
                }}

                if ('speechSynthesis' in window) {{
                    const utterance = new SpeechSynthesisUtterance("{escaped_text}");
                    utterance.lang = 'en-US';
                    utterance.rate = 0.9;
                    utterance.pitch = 1;

                    utterance.onstart = function() {{
                        isSpeaking = true;
                        button.textContent = '⏹️ Stop';
                        statusDiv.textContent = 'Speaking...';
                        statusDiv.style.color = 'green';
                    }};

                    utterance.onend = function() {{
                        isSpeaking = false;
                        button.textContent = '🔊 Speak';
                        statusDiv.textContent = 'Speech completed';
                        statusDiv.style.color = 'blue';
                    }};

                    utterance.onerror = function(event) {{
                        isSpeaking = false;
                        button.textContent = '🔊 Speak';
                        statusDiv.textContent = 'Speech synthesis error: ' + event.error;
                        statusDiv.style.color = 'red';
                    }};

                    speechSynthesis.speak(utterance);
                }} else {{
                    statusDiv.textContent = 'Speech synthesis not supported in this browser.';
                    statusDiv.style.color = 'red';
                }}
            }});
        }})();
    </script>
    """

    components.html(html_code, height=100)

def speak_last_response(chat_history):
    """Speak the last assistant response from chat history"""
    last_assistant_msg = next((msg for msg in reversed(chat_history) if msg["role"] == "assistant"), None)
    if last_assistant_msg:
        speak_text_component(last_assistant_msg["content"])
    else:
        components.html('<div style="color: orange;">No assistant message to speak.</div>', height=30)
