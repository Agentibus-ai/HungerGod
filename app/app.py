#!/usr/bin/env python3
"""
Entrypoint for running the Flask app.
Supports both module and script execution.
"""
import os, sys
if __name__ == '__main__' and __package__ is None:
    # when run as script, add project root to path and set package context
    pkg_root = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(pkg_root)
    sys.path.insert(0, project_root)
    __package__ = 'app'
from flask import Flask, request, render_template, session, jsonify
from flask_session import Session
import os
import stripe

from .config import SECRET_KEY, PIZZERIA, INFO, STRIPE_WEBHOOK_SECRET
from .rule_kb import responses_template
from .openai_funcs import handle_function_call
from .state_handler import get_state, set_state
from .menu_helpers import format_menu, best_match
from .ai_intent import understand
from .ai_rag import rag_response
from .cart_logic import cart_summary, confirm_order, do_checkout
from .utils import log_chat

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Chat handler
def respond(text):
    state = get_state()
    # If in the middle of detailed order flow, handle steps sequentially
    step = state.get('step')
    if step == 'await_name':
        name = text.strip()
        state.setdefault('pending_order', {})['name'] = name
        state['step'] = 'await_delivery_method'
        set_state(state)
        return f"Piacere di conoscerti, {name}! Preferisci consegna a domicilio o ritiro al locale?"
    if step == 'await_delivery_method':
        choice = text.lower()
        if 'domicilio' in choice or 'consegna' in choice:
            state['pending_order']['delivery'] = 'domicilio'
            state['step'] = 'await_address'
            set_state(state)
            return "Perfetto, per favore indicami l'indirizzo di consegna."
        state['pending_order']['delivery'] = 'ritiro'
        state['step'] = 'await_payment_method'
        set_state(state)
        return "Va benissimo, come preferisci pagare? Online o direttamente in pizzeria?"
    if step == 'await_address':
        address = text.strip()
        state['pending_order']['address'] = address
        state['step'] = 'await_payment_method'
        set_state(state)
        return "Grazie! Ora dimmi come preferisci pagare: online o in pizzeria?"
    if step == 'await_payment_method':
        pm = text.lower()
        if 'online' in pm or 'carta' in pm:
            state['pending_order']['payment'] = 'online'
        else:
            state['pending_order']['payment'] = 'in pizzeria'
        state['step'] = 'await_order_confirmation'
        set_state(state)
        # Build order summary
        summary, total = cart_summary(state['cart'])
        items_text = '\n'.join([f"• {n} x{q}" for n,q in summary.items()])
        delivery = state['pending_order'].get('delivery')
        address = state['pending_order'].get('address', '-')
        payment = state['pending_order'].get('payment')
        # Build a rich markdown summary with ChatGPT-style formatting
        customer = state['pending_order'].get('name', '')
        pay_label = 'Online' if payment=='online' else 'In pizzeria'
        mode_label = '📦 Consegna a domicilio' if delivery=='domicilio' else '🏁 Ritiro al locale'
        confirm_msg = f"""Ciao **{customer}**, ecco il riepilogo del tuo ordine:
## 📋 Riepilogo Ordine
{items_text}

💰 **Totale:** €{total:.2f}
🚚 **Modalità:** {mode_label}
📍 **Indirizzo:** {address if delivery=='domicilio' else '—'}
💳 **Pagamento:** {pay_label}

__Confermi l'ordine?___ (sì / no)"""
        return confirm_msg
    if step == 'await_order_confirmation':
        ans = text.strip().lower()
        if ans in ['sì','si','yes','confermo','ok']:
            state['step'] = 'ordered'
            set_state(state)
            # finalize checkout
            final = do_checkout(state)
            return f"✅ Ordine confermato!\n{final}"
        state['step'] = 'ordering'
        state.pop('pending_order', None)
        set_state(state)
        return "Ordine annullato. Posso aiutarti in altro modo?"

    if text == "!welcome" or state.get("step") == "start":
        state["step"] = "ordering"
        set_state(state)
        return f"👋 Benvenuto in *{PIZZERIA}*! Vuoi vedere il menu o ordinare subito? La Diavola oggi è 🔥"

    parsed_intents = understand(text, state)

    # Fallback: if no intent parsed, delegate to function-calling handler
    if not parsed_intents:
        return handle_function_call(text, state)

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
        # Show menu on 'menu' intent
        if intent == "menu":
            header = responses_template.get('menu', '📋 Ecco il nostro menu completo!')
            responses.append(f"{header}\n\n" + format_menu())
        # Acknowledge order intent and show menu
        elif intent == "order":
            # Conversational acknowledgement
            ack = responses_template.get(
                'order_start',
                "Ho capito, desideri fare un ordine. Ecco il nostro menu:"
            )
            responses.append(ack)
            responses.append(format_menu())
        elif intent in ["greet", "info"]:
            if intent == 'greet':
                responses.append(responses_template.get('greet', f"👋 Ciao! Benvenuto in {PIZZERIA}!"))
            else:
                responses.append(responses_template.get('info', f"📍 {INFO['address']}\n🕒 {INFO['hours']}\n📞 {INFO['phone']}"))
        elif intent == "track":
            lo = state.get("last_order")
            if lo:
                eta = lo.get('eta', '')
                tpl = responses_template.get('track', 'Il tuo ordine sarà pronto per il ritiro alle {eta}.')
                responses.append(tpl.format(eta=eta))
            else:
                responses.append(responses_template.get('fallback', 'Nessun ordine trovato. Vuoi ordinarne uno?'))
        elif intent == "staff":
            responses.append(responses_template.get('other', 'Ti metto in contatto con lo staff... scherzo! Sono ancora io. Dimmi pure.'))
        elif intent == "checkout":
            # Begin detailed order flow: collect customer info
            state['step'] = 'await_name'
            set_state(state)
            # Acknowledge and ask for customer name
            responses.append("Perfetto, proseguiamo con l'ordine! Prima di tutto, come ti chiami?")
        elif intent == "other":
            # Fallback for miscellaneous queries via function calling
            responses.append(handle_function_call(text, state))
    # If still no response, use function-calling fallback
    if not responses:
        responses.append(handle_function_call(text, state))

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
    # Persist chat to file for analytics
    try:
        log_chat(user_input, reply)
    except Exception:
        pass
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
    # Allow the port to be configured via the PORT env var (default 5000)
    port = int(os.environ.get("PORT", 5000))
    # Bind to all interfaces by default
    app.run(debug=True, host="0.0.0.0", port=port)