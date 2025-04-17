import os
import json
from dotenv import load_dotenv
import openai
import stripe

# Load environment variables and API keys
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

# Load menu data
BASE_DIR = os.path.dirname(__file__)
with open(os.path.join(BASE_DIR, "pizza_menu.json")) as f:
    menu = json.load(f)

# Constants
PIZZERIA = "Pizzeria Da Mario"
INFO = {"address": "Via Roma 123, Milano", "hours": "11:00 - 23:00", "phone": "+39 02 1234567"}
SECRET_KEY = os.getenv("SECRET_KEY", "SUPER_SECURE_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")