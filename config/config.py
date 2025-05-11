import os
from dotenv import load_dotenv

# Specify the path explicitly
dotenv_path = os.path.join(os.path.dirname(__file__), "..", ".env")
print(f"Loading .env file from: {dotenv_path}")

# Check if the file exists
if not os.path.exists(dotenv_path):
    raise FileNotFoundError(f".env file not found at path: {dotenv_path}")

# Load the .env file
load_dotenv(dotenv_path)

# Print all environment variables for debugging (Remove in production)
print("Environment Variables Loaded:")
for key, value in os.environ.items():
    if "KEY" in key or "SECRET" in key:
        print(f"{key} = {value}")

# Load API keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Debugging: Check if keys are loaded
print(f"OPENAI_API_KEY: {OPENAI_API_KEY}")
print(f"GEMINI_API_KEY: {GEMINI_API_KEY}")

# Validate the keys
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is not set")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is not set")
