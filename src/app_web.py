from flask import Flask, request, render_template, session, jsonify
from flask_session import Session
from openai import OpenAI
from dotenv import load_dotenv
from utils import save_order
import os, json, difflib, random, stripe, re
from datetime import datetime, timedelta

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "SUPER_SECURE_KEY")
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

with open("pizza_menu.json") as f:
    menu = json.load(f)

PIZZERIA = "Pizzeria Da Mario"
INFO = {"address": "Via Roma 123, Milano", "hours": "11:00 - 23:00", "phone": "+39 02 1234567"}

# State handling
get_state = lambda: session.setdefault("user_state", {"step": "start", "cart": [], "history": [], "name": "", "last_order": {}, "last_active": datetime.now()})
def set_state(s): session["user_state"] = s; session.modified = True

# Menu helpers
def format_menu():
    """Format the menu with improved styling and readability"""
    lines = [f"# 📋 *Menu di {PIZZERIA}*"]
    
    # Group menu items by category
    section_emojis = {"Pizze": "🍕", "Bevande": "🥤", "Dolci": "🍰"}
    
    for section, items in menu.items():
        emoji = section_emojis.get(section, "")
        lines.append(f"\n## {emoji} *{section}*")
        
        # Divide items into columns
        if section == "Pizze":
            for item in items:
                price_str = f"€{item['price']:.2f}"
                lines.append(f"- **{item['name']}** ─ {price_str}")
        else:
            for item in items:
                price_str = f"€{item['price']:.2f}"
                lines.append(f"- **{item['name']}** ─ {price_str}")
    
    lines.append("\n*Per ordinare, scrivi ad esempio:* _\"Una Margherita e una Coca-Cola\"_")
    return "\n".join(lines)


def best_match(name):
    if not name or len(name) < 2: return None
    all_items = [(n.lower(), i) for cat in menu.values() for i in cat for n in [i['name']] + i.get('aliases', [])]
    match = difflib.get_close_matches(name.lower(), [n for n,_ in all_items], n=1, cutoff=0.55)
    return next((i for n,i in all_items if n == match[0]), None) if match else None

def cart_summary(cart):
    out, total = {}, 0
    for item in cart: out[item['name']] = out.get(item['name'], 0)+1; total += item['price']
    return out, total

# OpenAI LLM intent parsing
def understand(text, state):
    recent = state["history"][-6:]
    chat_history = [f"{'Bot' if i % 2 == 0 else 'User'}: {m}" for i, m in enumerate(recent)]
    cart, _ = cart_summary(state["cart"])
    cart_text = "\n".join([f"{k} x{v}" for k, v in cart.items()]) or "Carrello vuoto"

    system_prompt = f"""
Sei Mario, un assistente virtuale italiano per {PIZZERIA}. Il tuo compito è analizzare il messaggio dell'utente
e restituire *una lista JSON* con tutte le intenzioni riconosciute e gli articoli menzionati.

Formato di output JSON:
[
  {{
    "intent": "add_to_cart",
    "items": [{{"name": "Coca-Cola", "quantity": 1}}]
  }},
  {{
    "intent": "remove",
    "items": [{{"name": "Diavola", "quantity": 1}}]
  }}
]

Valori validi per 'intent':
["add_to_cart", "remove", "order", "menu", "checkout", "greet", "info", "track", "staff", "other"]

Rispondi solo con un JSON valido. Nessuna spiegazione.
Contesto:
Carrello attuale:\n{cart_text}
Conversazione recente:\n{chr(10).join(chat_history)}
Messaggio utente:\n{text}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4-1106-preview",
            messages=[{"role": "system", "content": system_prompt}],
            temperature=0.2
        )
        content = response.choices[0].message.content.strip()
        match = re.search(r"(\[.*\])", content, re.DOTALL)
        return json.loads(match.group(1)) if match else []
    except Exception as e:
        print("LLM error:", e)
        return []


# Cart logic
def confirm_order(user_state, items_added=None):
    cart = user_state["cart"]
    if not cart:
        return (
            "🛒 Il tuo carrello è vuoto. "
            "Puoi dire 'menu' per vedere le nostre opzioni deliziose!"
        )

    summary, _ = cart_summary(cart)
    message = []

    if items_added:
        added_text = ", ".join([f"{n} x{q}" for (n, q) in items_added])
        message.append(f"✅ *Aggiunto*: {added_text}\n")

    message.append("🧾 *Il tuo ordine finora:*\n")
    for name, qty in summary.items():
        message.append(f"• {name} x{qty}")

    total = sum(item["price"] for item in cart)
    message.append(f"\n💰 *Totale*: €{total:.2f}")

    categories_in_cart = set()
    for item_name in summary.keys():
        for cat_name, cat_items in menu.items():
            if any(ci["name"] == item_name for ci in cat_items):
                categories_in_cart.add(cat_name.lower())

    missing_cats = []
    if "pizze" in categories_in_cart and "bevande" not in categories_in_cart:
        missing_cats.append("Bevande")
    if "bevande" in categories_in_cart and "dolci" not in categories_in_cart:
        missing_cats.append("Dolci")
    if "pizze" in categories_in_cart and "dolci" not in categories_in_cart:
        missing_cats.append("Dolci")

    if missing_cats:
        cat = random.choice(missing_cats)
        if cat in menu and len(menu[cat]) > 0:
            suggestion = random.choice(menu[cat])
            message.append(
                f"\n✨ *Aggiungiamo un* _{suggestion['name']}_ *per €{suggestion['price']:.2f}?* "
                f"È perfetto con la tua pizza!"
            )

    message.append("\nVuoi aggiungere altro o passiamo al checkout?")
    return "\n\n".join(message)

def generate_checkout(user_state):
    cart = user_state["cart"]
    if not cart:
        return "🛒 Il tuo carrello è vuoto. Vuoi ordinare qualcosa?"

    total = sum(i["price"] for i in cart)
    summary = get_cart_summary(cart)
    items_text = "\n".join([
        f"• {name} x{qty} (€{sum(i['price'] for i in cart if i['name'] == name):.2f})"
        for name, qty in summary.items()
    ])

    try:
        save_order("web_user", list(summary.keys())[0], len(cart))
    except Exception as e:
        print("Order saving error:", e)

    order_number = f"#{random.randint(1000,9999)}"
    eta = (datetime.now() + timedelta(minutes=random.randint(15,30))).strftime("%H:%M")

    user_state["cart"] = []
    user_state["last_order"] = {"number": order_number, "eta": eta, "total": total}
    user_state["step"] = "ordered"

    return (
        f"📋 *Order Summary*\n\n"
        f"{items_text}\n\n"
        f"💰 *Total*: €{total:.2f}\n"
        f"🕒 *Pickup*: {eta} presso {restaurant_info['address']}\n\n"
        f"✅ *Confirmed!* Ordine: {order_number}\n"
        f"Grazie per aver scelto {PIZZERIA_NAME}! 🍕"
    )


def do_checkout(state):
    """Generate a beautiful checkout summary"""
    if not state["cart"]: 
        return "🛒 *Il tuo carrello è vuoto.* Vuoi ordinare qualcosa?"
    
    c, total = cart_summary(state["cart"])
    
    lines = ["# 📋 *Riepilogo Ordine*\n"]
    
    lines.append("## Prodotti:")
    for name, qty in c.items():
        item_price = next(i['price'] for i in state['cart'] if i['name']==name)
        item_total = qty * item_price
        lines.append(f"- **{name}** × {qty} = €{item_total:.2f}")
    
    lines.append("\n---")
    lines.append(f"## *Totale:* €{total:.2f}")
    
    eta = (datetime.now() + timedelta(minutes=random.randint(15,30))).strftime("%H:%M")
    order_num = f"#{random.randint(1000,9999)}"
    
    lines.append("\n## Dettagli:")
    lines.append(f"- **Ordine:** {order_num}")
    lines.append(f"- **Ritiro:** *{eta}* presso {INFO['address']}")
    
    lines.append("\n## ✅ *Ordine Confermato!*")
    lines.append(f"\n*Grazie per aver scelto {PIZZERIA}!* 🍕 *Buon appetito!*")
    
    save_order("web_user", next(iter(c)), sum(c.values()))
    state.update({"cart":[], "last_order":{"number":order_num,"eta":eta,"total":total}, "step":"ordered"})
    
    return "\n".join(lines)

# Chat handler
def respond(text):
    state = get_state()
    if text == "!welcome" or state["step"] == "start":
        state["step"] = "ordering"
        set_state(state)
        return f"👋 Benvenuto in *{PIZZERIA}*! Vuoi vedere il menu o ordinare subito? La Diavola oggi è 🔥"

    parsed_intents = understand(text, state)
    if not parsed_intents:
        return "Non ho capito bene. Vuoi vedere il menu o ordinare qualcosa?"

    from collections import defaultdict
    intent_bucket = defaultdict(list)

    for action in parsed_intents:
        intent = action.get("intent")
        items = action.get("items", [])
        if intent in ["add_to_cart", "remove"]:
            for i in items:
                intent_bucket[intent].append(i)
        else:
            intent_bucket[intent] = items

    responses = []
    added = []
    removed = []

    if intent_bucket.get("add_to_cart"):
        combined = defaultdict(int)
        for i in intent_bucket["add_to_cart"]:
            combined[i["name"]] += i.get("quantity", 1)
        for name, qty in combined.items():
            match = best_match(name)
            if match:
                for _ in range(qty):
                    state['cart'].append(match)
                added.append((match["name"], qty))
            else:
                responses.append(f"'{name}' non è nel nostro menu. Vuoi che ti mostri le opzioni?")

    if intent_bucket.get("remove"):
        for i in intent_bucket["remove"]:
            name = i['name']
            qty = i.get('quantity', 1)
            matches = [x for x in state['cart'] if x['name'].lower() == name.lower()]
            for m in matches[:qty]:
                state['cart'].remove(m)
                removed.append(name)

    set_state(state)

    if added:
        responses.append(confirm_order(state, added))
    if removed:
        c, _ = cart_summary(state['cart'])
        if c:
            left = ", ".join([f"{k} x{v}" for k, v in c.items()])
            responses.append(f"🗑️ Ho rimosso {', '.join(set(removed))}. Carrello attuale: {left}")
        else:
            responses.append("Il tuo carrello è ora vuoto.")

    # Handle other intents
    for intent, data in intent_bucket.items():
        if intent in ["add_to_cart", "remove"]:
            continue
        if intent == "menu":
            responses.append(format_menu())
        elif intent in ["greet", "info"]:
            responses.append(
                f"📍 {INFO['address']}\n🕒 {INFO['hours']}\n📞 {INFO['phone']}\n"
                "Vuoi vedere il nostro menu o iniziare un ordine?"
            )
        elif intent == "track":
            lo = state.get("last_order")
            if lo:
                responses.append(f"Il tuo ordine {lo['number']} sarà pronto alle {lo['eta']}!")
            else:
                responses.append("Nessun ordine trovato. Vuoi ordinarne uno?")
        elif intent == "staff":
            responses.append("Ti metto in contatto con lo staff... scherzo! Sono ancora io. Dimmi pure.")
        elif intent == "checkout":
            responses.append(do_checkout(state))
            set_state(state)
        elif intent == "other":
            responses.append("Non ho capito bene. Vuoi vedere il menu, ordinare o controllare un ordine?")

    return "\n\n".join(responses)


@app.route("/")
def index(): return render_template("chat.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.json.get("message", "")
    reply = respond(user_input)
    state = get_state()
    state["history"].append(reply)
    set_state(state)
    return jsonify({"response": reply, "cart": state["cart"]})

@app.route("/stripe-webhook", methods=["POST"])
def stripe_webhook():
    try:
        event = stripe.Webhook.construct_event(request.data, request.headers.get("stripe-signature"), os.getenv("STRIPE_WEBHOOK_SECRET"))
        if event["type"] == "checkout.session.completed": print("Payment completed:", event["data"]["object"])
    except Exception as e:
        print("Webhook error:", e)
        return "Error", 400
    return "OK", 200

if __name__ == "__main__":
    app.run(debug=True, port=5000)