import os
from typing import Optional

# Setup Gemini Client (using the official google-genai package)
client = None
try:
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        from google import genai
        # Initialize the official SDK client. It automatically picks up proxy configurations
        # and standard API limits for standard key validation.
        client = genai.Client(api_key=api_key)
except ImportError:
    # Safely degrade if package is missing in execution path
    print("Warning: google-genai package not found. Continuing with mock fallback mode.")
except Exception as e:
    print(f"Warning: Failed to initialize Gemini Client: {e}")


def generate_with_gemini(prompt: str, fallback_content: str) -> str:
    """
    Abstractions wrapper for calling Gemini 2.5 Flash.
    If the API Key is invalid, or the client is not initialized, or the API call limits/errors
    out, it outputs the high-quality predefined fallback layout so the application never breaks.

    Design rationale:
      Using gemini-2.5-flash for standard code and blueprint generation tasks as it is 
      cost-effective, has low latency, and is highly optimized for text generation.
    """
    if client:
        try:
            # Invoking Google GenAI Client with standard parameters
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            )
            if response.text:
                return response.text.strip()
        except Exception as e:
            # Graceful logging and fallback execution
            print(f"Gemini API invocation failed ({e}). Reverting to fallback template.")
    
    return fallback_content
