import openai

from .config import PIZZERIA
from .kb import kb

def rag_response(text, state):
    """
    Retrieval-Augmented Generation fallback: retrieve relevant KB docs and generate answer.
    """
    # Retrieve top docs
    docs = kb.query(text, top_k=3)
    context = "\n\n".join([d['text'] for d in docs])

    # Build recent conversation context (last 10 messages)
    # Build recent conversation context (last 10 messages)
    recent = state.get("history", [])[-10:]
    messages = []
    for msg in recent:
        # Support both new dict entries and legacy string entries
        if isinstance(msg, dict):
            r = msg.get('role', 'assistant')
            role = 'assistant' if r == 'assistant' else 'user'
            content = msg.get('content', '')
        else:
            # Legacy string entry: assume assistant message
            role = 'assistant'
            content = msg
        messages.append({"role": role, "content": content})

    # Prepend system prompt with KB context
    system_prompt = (
        f"Sei Mario, un assistente virtuale per {PIZZERIA}. "
        "Usa le seguenti informazioni se pertinenti per rispondere:\n" + context
    )
    all_messages = [{"role": "system", "content": system_prompt}] + messages + [
        {"role": "user", "content": text}
    ]

    response = openai.chat.completions.create(
        model="gpt-4-1106-preview",
        messages=all_messages,
        temperature=0.3
    )
    return response.choices[0].message.content.strip()