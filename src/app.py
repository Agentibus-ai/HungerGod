from flask import Flask, request
import requests
import random
from utils import save_order
import json

app = Flask(__name__)

VERIFY_TOKEN = "pizza_time"
ACCESS_TOKEN = ""
PHONE_NUMBER_ID = ""

# Temporary in-memory state
user_state = {}

pizza_jokes = [
    "Why did the pizza maker quit his job? He just couldn't make ends 'meat'!",
    "You can't make everyone happy... you're not pizza!",
    "I'm on a seafood diet. I see food and I eat it—especially if it's pizza."
]

with open("pizza_menu.json") as f:
    menu = json.load(f)

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        if request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return request.args.get("hub.challenge"), 200
        return "Verification failed", 403

    data = request.get_json()
    for entry in data.get("entry", []):
        for change in entry.get("changes", []):
            if "messages" in change["value"]:
                msg = change["value"]["messages"][0]
                sender = msg["from"]
                text = msg["text"]["body"].lower()
                reply = handle_user_message(sender, text)
                send_whatsapp_message(sender, reply)
    return "ok", 200

def handle_user_message(sender, text):
    if sender not in user_state:
        user_state[sender] = {"step": "greeting"}

    state = user_state[sender]

    if state["step"] == "greeting":
        user_state[sender]["step"] = "size"
        joke = random.choice(pizza_jokes)
        sizes = "\n- ".join(menu["sizes"])
        return f"Welcome to *PizzaBot*! 🍕\n{joke}\n\nLet’s make your taste buds dance! What size pizza are you craving today?\n- {sizes}"

    elif state["step"] == "size":
        user_state[sender]["size"] = text
        user_state[sender]["step"] = "topping"
        toppings = "\n- ".join(menu["toppings"])
        return f"Yum! And what topping would you love to add?\n- {toppings}"

    elif state["step"] == "topping":
        user_state[sender]["topping"] = text
        user_state[sender]["step"] = "confirm"
        size = user_state[sender]["size"]
        topping = user_state[sender]["topping"]
        return f"Alright! So you’re going for a *{size.capitalize()} {topping.capitalize()}* pizza. That’s a masterpiece in the making. Shall I place the order? (yes/no)"

    elif state["step"] == "confirm":
        if "yes" in text:
            order = user_state[sender]
            save_order(sender, order["size"], order["topping"])
            user_state[sender] = {"step": "greeting"}  # reset
            return f"🔥 Order Confirmed! Your *{order['size'].capitalize()} {order['topping'].capitalize()}* pizza is entering the oven.\nSit tight, flavor is coming your way! 🍕🚀"
        else:
            user_state[sender] = {"step": "greeting"}
            return "No worries! Cravings change, just like toppings. Want to start a new order? Say anything!"

    return "Oops, I didn’t catch that. Type anything to begin a fresh pizza journey!"

def send_whatsapp_message(recipient, message):
    url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "messaging_product": "whatsapp",
        "to": recipient,
        "type": "text",
        "text": {"body": message}
    }
    r = requests.post(url, headers=headers, json=data)
    return r.json()

if __name__ == "__main__":
    app.run(port=5000, debug=True)
