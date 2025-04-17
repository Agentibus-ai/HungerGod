from flask import session
from datetime import datetime

def get_state():
    """
    Retrieve or initialize the user's session state.
    """
    return session.setdefault(
        "user_state",
        {
            "step": "start",
            "cart": [],
            "history": [],
            "name": "",
            "last_order": {},
            "last_active": datetime.now(),
        },
    )

def set_state(s):
    """
    Persist the updated state back into the session.
    """
    session["user_state"] = s
    session.modified = True