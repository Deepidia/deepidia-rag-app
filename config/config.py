import os
from dotenv import load_dotenv

# Get the project root directory (where app.py is located)
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dotenv_path = os.path.join(project_root, ".env")
print(f"Loading .env file from: {dotenv_path}")

# Debug: Check if file exists and its size
if os.path.exists(dotenv_path):
    file_size = os.path.getsize(dotenv_path)
    print(f".env file exists with size: {file_size} bytes")
else:
    raise FileNotFoundError(f".env file not found at path: {dotenv_path}")

# Load the .env file
load_dotenv(dotenv_path, override=True)

# Load API keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Validate the keys
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is not set")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is not set")

