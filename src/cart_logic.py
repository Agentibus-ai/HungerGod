import random
from datetime import datetime, timedelta

from config import menu, PIZZERIA, INFO
from utils import save_order

def cart_summary(cart):
    """Return a summary dict of item counts and the total price."""
    out = {}
    total = 0
    for item in cart:
        out[item["name"]] = out.get(item["name"], 0) + 1
        total += item["price"]
    return out, total

def confirm_order(user_state, items_added=None):
    """
    Generate a confirmation message after items are added/removed.
    """
    cart = user_state.get("cart", [])
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

    # Suggestive upsell
    categories_in_cart = set()
    for item_name in summary.keys():
        for cat_name, cat_items in menu.items():
            if any(ci["name"] == item_name for ci in cat_items):
                categories_in_cart.add(cat_name.lower())

    missing_cats = []
    if "pizze" in categories_in_cart and "bevande" not in categories_in_cart:
        missing_cats.append("Bevande")
    if ("bevande" in categories_in_cart or "pizze" in categories_in_cart) and "dolci" not in categories_in_cart:
        missing_cats.append("Dolci")

    if missing_cats:
        cat = random.choice(missing_cats)
        if cat in menu and menu[cat]:
            suggestion = random.choice(menu[cat])
            message.append(
                f"\n✨ *Aggiungiamo un* _{suggestion['name']}_ *per €{suggestion['price']:.2f}?* "
                f"È perfetto con la tua pizza!"
            )

    message.append("\nVuoi aggiungere altro o passiamo al checkout?")
    return "\n\n".join(message)

def do_checkout(state):
    """
    Generate a beautiful checkout summary and clear the cart.
    """
    cart = state.get("cart", [])
    if not cart:
        return "🛒 *Il tuo carrello è vuoto.* Vuoi ordinare qualcosa?"

    c, total = cart_summary(cart)
    lines = ["# 📋 *Riepilogo Ordine*\n"]

    lines.append("## Prodotti:")
    for name, qty in c.items():
        item_price = next(i["price"] for i in cart if i["name"] == name)
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

    # Persist order
    save_order("web_user", next(iter(c)), sum(c.values()))
    state.update({"cart": [], "last_order": {"number": order_num, "eta": eta, "total": total}, "step": "ordered"})
    return "\n".join(lines)