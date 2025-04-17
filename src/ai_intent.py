import json
import re
import openai
from cart_logic import cart_summary
from config import PIZZERIA

def understand(text, state):
    """
    Use an LLM to parse user text into structured intents and items.
    """
    # Keep a rolling window of the last 6 messages (user and bot)
    recent_msgs = state.get("history", [])[-6:]
    chat_history = []
    for msg in recent_msgs:
        if isinstance(msg, dict):
            # New-style entry with role/content
            role = "Bot" if msg.get("role") == "assistant" else "User"
            content = msg.get("content", "")
        else:
            # Legacy string entry: assume assistant message
            role = "Bot"
            content = msg
        chat_history.append(f"{role}: {content}")
    cart, _ = cart_summary(state.get("cart", []))
    cart_text = "\n".join([f"{k} x{v}" for k, v in cart.items()]) or "Carrello vuoto"

    # Build system prompt for intent parsing
    last_order = state.get("last_order", {})
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
Ultimo ordine:\n{last_order}
Messaggio utente:\n{text}
    """
    try:
        response = openai.chat.completions.create(
            model="gpt-4-1106-preview",
            messages=[{"role": "system", "content": system_prompt}],
            temperature=0.2
        )
        content = response.choices[0].message.content.strip()
        print("LLM raw response:", content)
        match = re.search(r"(\[.*\])", content, re.DOTALL)
        return json.loads(match.group(1)) if match else []
    except Exception as e:
        print("LLM error:", e)
        return []