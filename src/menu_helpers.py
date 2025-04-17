import difflib
from config import menu, PIZZERIA

def format_menu():
    """Format the menu with improved styling and readability"""
    lines = [f"# 📋 *Menu di {PIZZERIA}*"]

    section_emojis = {"Pizze": "🍕", "Bevande": "🥤", "Dolci": "🍰"}

    for section, items in menu.items():
        emoji = section_emojis.get(section, "")
        lines.append(f"\n## {emoji} *{section}*")

        for item in items:
            price_str = f"€{item['price']:.2f}"
            lines.append(f"- **{item['name']}** ─ {price_str}")

    lines.append(
        "\n*Per ordinare, scrivi ad esempio:* _\"Una Margherita e una Coca-Cola\"_"
    )
    return "\n".join(lines)

def best_match(name):
    """Find the closest matching menu item by name or alias."""
    if not name or len(name) < 2:
        return None
    all_items = []
    for cat_items in menu.values():
        for item in cat_items:
            all_items.append((item["name"].lower(), item))
            for alias in item.get("aliases", []):
                all_items.append((alias.lower(), item))
    names = [n for n, _ in all_items]
    matches = difflib.get_close_matches(name.lower(), names, n=1, cutoff=0.55)
    if matches:
        match_name = matches[0]
        for n, item in all_items:
            if n == match_name:
                return item
    return None