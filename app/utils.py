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
   
def log_chat(user_message, bot_reply):
    """
    Append a chat entry (user and bot messages with timestamp) to logs/chat.log.
    """
    try:
        # Ensure logs directory exists
        if not os.path.exists("logs"):
            os.makedirs("logs")
        entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "user": user_message,
            "bot": bot_reply,
        }
        with open("logs/chat.log", "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        print(f"Error logging chat: {e}")