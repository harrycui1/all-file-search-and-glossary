import os

# Google Gemini API Key - set via environment variable
# export GEMINI_API_KEY="your-api-key-here"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# Model to use for querying
MODEL_NAME = "gemini-3-pro-preview"

# File Search Store name (will be set after creation)
STORE_NAME = ""

# Data paths
KANGYUR_BASE = os.path.join(
    os.path.dirname(__file__),
    "KANGYUR updated to 12 30 25 WS 2"
)

# POC test folder
POC_FOLDER = os.path.join(KANGYUR_BASE, "1. 'DUL BA_Vowed Morality (Vinaya)")
