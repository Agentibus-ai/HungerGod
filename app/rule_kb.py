import os
import json

from .config import BASE_DIR, menu

# Path to the Italian KB file
KB_PATH = os.path.join(BASE_DIR, 'italian_kb.json')

# Load the KB JSON, which is an array: first items are utterance-intent pairs, last element is config
with open(KB_PATH, 'r', encoding='utf-8') as f:
    raw = json.load(f)

# Separate utterances and config
utterances = []
categories = {}
actions = {}
quantifiers = []
responses_template = {}
for entry in raw:
    if isinstance(entry, dict) and 'intent' in entry and 'utterance' in entry:
        utterances.append(entry)
    elif isinstance(entry, dict) and 'categories' in entry:
        # config block
        categories = entry.get('categories', {})
        actions = entry.get('actions', {})
        quantifiers = entry.get('quantifiers', [])
        responses_template = entry.get('responses_template', {})

def classify(text):
    """
    Simple rule-based classifier using the Italian KB.
    Returns a list of dicts: [{"intent": intent, "items": [{name, quantity} ...]}]
    """
    text_l = text.lower()
    results = []
    # Check utterance patterns first
    for u in utterances:
        utt = u['utterance'].lower()
        if utt == text_l or utt in text_l:
            intent = u['intent']
            items = []
            # Extract items if relevant
            if intent in ('order', 'add_to_cart', 'remove'):
                for cat_items in menu.values():
                    for item in cat_items:
                        terms = [item['name']] + item.get('aliases', [])
                        for term in terms:
                            if term.lower() in text_l:
                                items.append({"name": item['name'], "quantity": 1})
                                break
                # Treat 'order' with items as add_to_cart
                if intent == 'order' and items:
                    intent = 'add_to_cart'
            results.append({"intent": intent, "items": items})
    if results:
        return results
    # Fallback: check simple action keywords
    for intent, kws in actions.items():
        for kw in kws:
            if kw in text_l:
                items = []
                if intent in ('order', 'add_to_cart', 'remove'):
                    for cat_items in menu.values():
                        for item in cat_items:
                            terms = [item['name']] + item.get('aliases', [])
                            for term in terms:
                                if term.lower() in text_l:
                                    items.append({"name": item['name'], "quantity": 1})
                                    break
                    if intent == 'order' and items:
                        intent = 'add_to_cart'
                return [{"intent": intent, "items": items}]
    # No rule-based match
    return []