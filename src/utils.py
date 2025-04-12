import json
import os

ORDER_FILE = "orders.json"


def save_order(phone_number, size, topping):
    order_data = {
        "phone": phone_number,
        "size": size,
        "topping": topping,
    }
    if not os.path.exists(ORDER_FILE):
        with open(ORDER_FILE, "w") as f:
            json.dump([], f)
    with open(ORDER_FILE, "r+") as f:
        data = json.load(f)
        data.append(order_data)
        f.seek(0)
        json.dump(data, f, indent=2)


def load_orders():
    if os.path.exists(ORDER_FILE):
        with open(ORDER_FILE, "r") as f:
            return json.load(f)
    return []
