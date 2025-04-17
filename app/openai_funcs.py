import json
import openai

from .config import PIZZERIA, INFO
from .menu_helpers import format_menu, best_match
from .cart_logic import cart_summary, confirm_order, do_checkout
from .ai_rag import rag_response
from .state_handler import set_state

# Define available functions for OpenAI function calling
function_definitions = [
    {
        "name": "show_menu",
        "description": "Get the formatted restaurant menu",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_info",
        "description": "Get restaurant address, hours, and phone number",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "add_to_cart",
        "description": "Add an item and quantity to the cart",
        "parameters": {
            "type": "object",
            "properties": {
                "item": {"type": "string"},
                "quantity": {"type": "integer"},
            },
            "required": ["item"],
        },
    },
    {
        "name": "remove_from_cart",
        "description": "Remove an item and quantity from the cart",
        "parameters": {
            "type": "object",
            "properties": {
                "item": {"type": "string"},
                "quantity": {"type": "integer"},
            },
            "required": ["item"],
        },
    },
    {
        "name": "checkout",
        "description": "Finalize the order and provide summary",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "track_order",
        "description": "Get the status of the last order",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "rag_fallback",
        "description": "Fallback answer via retrieval-augmented generation",
        "parameters": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    },
]

# Map function names to Python implementations
def fn_show_menu(args, state):
    return format_menu(), state

def fn_get_info(args, state):
    info = f"📍 {INFO['address']}\n🕒 {INFO['hours']}\n📞 {INFO['phone']}"
    return info, state

def fn_add_to_cart(args, state):
    name = args.get('item', '')
    qty = int(args.get('quantity', 1))
    match = best_match(name)
    if not match:
        return f"Mi dispiace, '{name}' non è nel menu.", state
    for _ in range(qty):
        state['cart'].append(match)
    items_added = [(match['name'], qty)]
    reply = confirm_order(state, items_added)
    return reply, state

def fn_remove_from_cart(args, state):
    name = args.get('item', '')
    qty = int(args.get('quantity', 1))
    removed = []
    matches = [x for x in state['cart'] if x['name'].lower() == name.lower()]
    for m in matches[:qty]:
        state['cart'].remove(m)
        removed.append(name)
    if removed:
        reply = f"🗑️ Ho rimosso {', '.join(removed)} dal carrello."
    else:
        reply = f"Non ho trovato '{name}' nel tuo carrello."
    return reply, state

def fn_checkout(args, state):
    reply = do_checkout(state)
    return reply, state

def fn_track_order(args, state):
    lo = state.get('last_order', {})
    if lo:
        eta = lo.get('eta', '')
        return f"Il tuo ordine {lo.get('number','')} sarà pronto alle {eta}.", state
    return "Nessun ordine recente trovato.", state

def fn_rag_fallback(args, state):
    query = args.get('query', '')
    reply = rag_response(query, state)
    return reply, state

# Name -> function map
handlers = {
    'show_menu': fn_show_menu,
    'get_info': fn_get_info,
    'add_to_cart': fn_add_to_cart,
    'remove_from_cart': fn_remove_from_cart,
    'checkout': fn_checkout,
    'track_order': fn_track_order,
    'rag_fallback': fn_rag_fallback,
}

def handle_function_call(text, state):
    # Build messages: system + history + user
    messages = [
        {"role": "system", "content": f"Sei Mario, assistente di {PIZZERIA}. Usa le funzioni disponibili per aiutare l'utente."}
    ]
    # Include recent history
    for msg in state.get('history', [])[-6:]:
        if isinstance(msg, dict):
            messages.append({"role": msg.get('role', 'user'), "content": msg.get('content', '')})
        else:
            messages.append({"role": "assistant", "content": msg})
    # User message
    messages.append({"role": "user", "content": text})

    # Call OpenAI with function definitions
    response = openai.chat.completions.create(
        model="gpt-4-1106-preview",
        messages=messages,
        functions=function_definitions,
        function_call="auto",
    )
    msg = response.choices[0].message
    # Check if the model requested a function call
    function_call = getattr(msg, 'function_call', None)
    if function_call:
        # Extract function name and arguments
        name = function_call.name
        args = json.loads(function_call.arguments or '{}')
        # Execute local handler
        handler = handlers.get(name)
        if handler:
            result, new_state = handler(args, state)
            # Persist updated state
            set_state(new_state)
        else:
            result = f"Funzione '{name}' non riconosciuta."
        # Append function call and result to messages
        # Append the function call message to the conversation
        messages.append({
            'role': 'assistant',
            'content': None,
            'function_call': {
                'name': name,
                'arguments': function_call.arguments,
            }
        })
        messages.append({
            'role': 'function',
            'name': name,
            'content': json.dumps(result),
        })
        # Ask model to respond after function call
        second = openai.chat.completions.create(
            model="gpt-4-1106-preview",
            messages=messages,
            temperature=0.3,
        )
        return second.choices[0].message.content
    # If no function call was made, fallback to RAG
    return rag_response(text, state)