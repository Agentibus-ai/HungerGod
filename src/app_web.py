from flask import Flask, request, render_template, session, jsonify
from flask_session import Session
import os
import stripe

from config import SECRET_KEY, PIZZERIA, INFO, STRIPE_WEBHOOK_SECRET
from state_handler import get_state, set_state
from menu_helpers import format_menu, best_match
from ai_intent import understand
from ai_rag import rag_response
from cart_logic import cart_summary, confirm_order, do_checkout

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Chat handler
def respond(text):
    state = get_state()

    if text == "!welcome" or state.get("step") == "start":
        state["step"] = "ordering"
        set_state(state)
        return f"👋 Benvenuto in *{PIZZERIA}*! Vuoi vedere il menu o ordinare subito? La Diavola oggi è 🔥"

    parsed_intents = understand(text, state)

    # Fallback: if no intent parsed, try to infer based on vague responses
    # If we couldn't parse any intent, try simple commands then fallback to RAG
    if not parsed_intents:
        text_lower = text.strip().lower()
        affirmatives = {
            "yes", "sure", "go", "vai", "ok", "okay",
            "checkout", "ordine", "order", "procedi", "confirm",
            "checkout now", "do it", "sì", "si", "va bene", "d'accordo"
        }
        if text_lower in affirmatives:
            if state.get("cart") and state.get("step") != "ordered":
                return do_checkout(state)
            return "Vuoi vedere il menu o iniziare un ordine?"
        if text_lower in {"menu", "show menu", "mostra menu"}:
            return format_menu()
        # Fallback to retrieval-augmented generation
        return rag_response(text, state)

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
                    state["cart"].append(match)
                added.append((match["name"], qty))
            else:
                responses.append(f"'{name}' non è nel nostro menu. Vuoi che ti mostri le opzioni?")

    if intent_bucket.get("remove"):
        for i in intent_bucket["remove"]:
            name = i["name"]
            qty = i.get("quantity", 1)
            matches = [x for x in state["cart"] if x["name"].lower() == name.lower()]
            for m in matches[:qty]:
                state["cart"].remove(m)
                removed.append(name)

    set_state(state)

    if added:
        responses.append(confirm_order(state, added))
    if removed:
        c, _ = cart_summary(state["cart"])
        if c:
            left = ", ".join([f"{k} x{v}" for k, v in c.items()])
            responses.append(f"🗑️ Ho rimosso {', '.join(set(removed))}. Carrello attuale: {left}")
        else:
            responses.append("Il tuo carrello è ora vuoto.")

    # Handle other intents
    for intent, data in intent_bucket.items():
        if intent in ["add_to_cart", "remove"]:
            continue
        # Show menu on 'menu' or 'order' intent
        if intent in ["menu", "order"]:
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
            # Retrieval-augmented response for unrecognized intent
            responses.append(rag_response(text, state))
    # If still no response, use RAG fallback
    if not responses:
        responses.append(rag_response(text, state))

    return "\n\n".join(responses)


@app.route("/")
def index():
    return render_template("chat.html")


@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.json.get("message", "")
    # Log user message
    state = get_state()
    state.setdefault("history", []).append({"role": "user", "content": user_input})
    set_state(state)
    # Generate response
    reply = respond(user_input)
    # Log assistant message
    state = get_state()
    state.setdefault("history", []).append({"role": "assistant", "content": reply})
    set_state(state)
    return jsonify({"response": reply, "cart": state.get("cart", [])})


@app.route("/stripe-webhook", methods=["POST"])
def stripe_webhook():
    try:
        sig_header = request.headers.get("stripe-signature")
        event = stripe.Webhook.construct_event(
            request.data, sig_header, STRIPE_WEBHOOK_SECRET
        )
        if event["type"] == "checkout.session.completed":
            print("Payment completed:", event["data"]["object"])
    except Exception as e:
        print("Webhook error:", e)
        return "Error", 400
    return "OK", 200


@app.route("/health")
def health():
    return "OK", 200

if __name__ == "__main__":
    app.run(debug=True, port=5000)