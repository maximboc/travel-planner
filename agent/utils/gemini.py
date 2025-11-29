import os
import time
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from dotenv import load_dotenv

load_dotenv()

LOCAL_JUDGE_FALLBACK = "llama3.1:8b"

GEMINI_FALLBACK_ORDER = [
    # "gemini-2.5-pro",
    # "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-2.0-flash-001",
    # "gemini-1.5-flash",
]


def setup_gemini():
    """Ensure API key is present."""
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return None
    return api_key


def get_gemini_model(temperature: float = 0):
    """
    Returns a configured LLM object. Tries preferred Gemini model, then fallbacks,
    and finally falls back to local Llama if all API models fail.
    """

    api_key = setup_gemini()

    # 1. Try Google Gemini Models
    if api_key:
        print(f"✨ Starting Gemini initialization attempts...")
        for model in GEMINI_FALLBACK_ORDER:
            try:
                print(f"🔄 Attempting to initialize: {model}")
                llm = ChatGoogleGenerativeAI(
                    model=model,
                    google_api_key=api_key,
                    temperature=temperature,
                    max_retries=1,
                )
                # Test connectivity/initialization
                llm.invoke("Test")
                print(f"✅ Successfully initialized model: {model}")
                return llm, model
            except Exception as e:
                print(f"⚠️ Model {model} failed: {e}")
                time.sleep(1)
                continue

        print("❌ All configured Gemini models failed or exhausted.")
    else:
        print("⚠️ Gemini API key not found. Skipping API attempts.")

    # 2. Final Fallback: Local Llama
    print(f"🔌 Switching to Local Fallback: {LOCAL_JUDGE_FALLBACK}")
    try:
        llm = ChatOllama(model=LOCAL_JUDGE_FALLBACK, temperature=temperature)
        # Test connectivity for local model
        llm.invoke("Test")
        print(f"✅ Successfully initialized local model: {LOCAL_JUDGE_FALLBACK}")
        return llm, LOCAL_JUDGE_FALLBACK

    except Exception as e:
        # If even local fails, we have a critical error
        raise RuntimeError(
            f"❌ CRITICAL: Both Gemini and Local Fallback failed. Error: {e}"
        )
