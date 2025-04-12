# HungerGod 🍽️

**HungerGod** is a pluggable, production-ready WhatsApp ordering bot template. Originally designed for pizza ordering, it's flexible enough for food, grocery, or even chai delivery bots.

---


## Structure (Under /src)

```
.
├── app.py               # Main Flask app with WhatsApp webhook handling
├── utils.py             # Helper functions for order saving/loading
├── pizza_menu.json      # Configurable menu for size and toppings
├── orders.json          # File-based order history
├── wsgi.py              # Entrypoint for production servers (e.g., Gunicorn)
├── requirements.txt     # Python dependencies
├── README.md            # You're reading it
```

---

## Local Setup

```bash
git clone https://github.com/Agentibus-ai/HungerGod
cd HungerGod
pip install -r requirements.txt
python app.py
```

### Test with ngrok:
```bash
ngrok http 5000
```
Copy the HTTPS URL and set it as your Meta webhook URL.

---

## Production Deployment (Render)

### 1. Add `requirements.txt` and `wsgi.py`
```bash
pip freeze > requirements.txt
```
**wsgi.py**
```python
from app import app
if __name__ == '__main__':
    app.run()
```

### 2. Push to GitHub
```bash
git init
git add .
git commit -m "initial commit"
git remote add origin https://github.com/yourusername/HungerGod.git
git push -u origin main
```

### 3. Deploy on [Render](https://render.com)
- New Web Service
- Connect GitHub repo
- Environment: Python 3
- Start Command:
  ```bash
  gunicorn wsgi:app
  ```

### 4. Done!
You’ll get a URL like:
```
https://hungergod.onrender.com
```
Use it to configure your WhatsApp webhook when you're ready.

---

## Next Steps
- Add a database (e.g., MongoDB, Firebase)
- Build a dashboard to view & manage orders
- Use LLM for smart intent detection (e.g., OpenAI, Rasa)
- Add payment integrations (Stripe, Razorpay)
- Support buttons, quick replies, and media messages

---

*"Gods need temples. HungerGod needs servers."*
