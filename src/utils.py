import datetime
import os
import json

def save_order(user_id, main_item, item_count):
    """
    Simple function to save order data for demo purposes
    """
    try:
        # Create logs directory if it doesn't exist
        if not os.path.exists("logs"):
            os.makedirs("logs")
            
        # Prepare order data
        order_data = {
            "user_id": user_id,
            "main_item": main_item,
            "total_items": item_count,
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        # Save to a log file
        with open("logs/orders.log", "a") as f:
            f.write(json.dumps(order_data) + "\n")
            
        return True
    except Exception as e:
        print(f"Error saving order: {e}")
        return False