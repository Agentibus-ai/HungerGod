# HungerGod 🍕

**HungerGod** is a production-ready, pluggable ordering assistant designed for restaurants.
Built for WhatsApp and Web, it brings intelligent, conversation-based food ordering to life — starting with pizza, but scalable to groceries, chai, desserts, and more.

Powered by **Flask**, enhanced with **LLMs**, integrated with **Stripe**, and deployable in minutes with **Render**.

---

## ⚙️ Project Structure

```
.
├── app/                # Python package with application code & data
│   ├── app.py          # Flask entrypoint (routes & respond logic)
│   ├── wsgi.py         # WSGI app for production servers
│   ├── config.py       # Environment loading, constants, API keys
│   ├── state_handler.py# Session state getters/setters
│   ├── menu_helpers.py # Menu formatting & best-match lookup
│   ├── cart_logic.py   # Cart summary & confirmation logic
│   ├── ai_intent.py    # Intent parsing (LLM + rule-based fallback)
│   ├── rule_kb.py      # Rule-based classifier using italian_kb.json
│   ├── openai_funcs.py # OpenAI function-calling integration
│   ├── ai_rag.py       # Retrieval-augmented generation fallback
│   ├── kb.py           # Knowledge-base loader & vector search helper
│   ├── utils.py        # Order & chat logging helpers
│   ├── pizza_menu.json # JSON menu data
│   └── italian_kb.json # Rule KB: utterances, templates, categories
├── templates/          # Jinja2 HTML templates
│   └── chat.html       # Chat UI
├── static/             # Static assets (CSS, JS)
│   ├── style.css
│   └── chatbot.js
├── logs/               # Persisted logs
│   ├── orders.log      # Order events log
│   └── chat.log        # Conversation log
├── Procfile            # Render/Heroku startup command
├── requirements.txt    # Python dependencies
├── README.md           # Project documentation
└── LICENSE             # License file
```

---

## 🚀 Local Setup

```bash
# Clone the repository and navigate to the project root
git clone https://github.com/Agentibus-ai/HungerGod.git
cd HungerGod

# (Optional) Create a .env file with your secrets:
cat > .env <<EOF
SECRET_KEY=your-secret-key
OPENAI_API_KEY=your-openai-key
STRIPE_SECRET_KEY=your-stripe-secret
STRIPE_WEBHOOK_SECRET=your-webhook-secret
EOF

# Install dependencies
pip install -r requirements.txt

# Run in development mode
export FLASK_ENV=development
python -m app.app
```

## ☁️ Production Deployment: [Render](https://hungergod.onrender.com/) 
1. In Render, create a new Web Service and point it to this repository.
2. Ensure *Root Directory* is **empty** (use the repo root), not `app/`.
3. Set *Build Command* to:
   ```bash
   pip install -r requirements.txt
   ```
4. Leave *Start Command* blank so that Render uses the `Procfile` in the root.
5. Your `Procfile` defines:
   ```
   web: gunicorn app.app:app --bind 0.0.0.0:$PORT
   ```
6. (Optional) Configure environment variables in your Render dashboard to match your `.env`.

## 🧠 Features
- ✅ Web-based UI (chat + menu + cart)
- 🧾 Dynamic JSON-based menu
- 🧠 LLM-powered intent parsing (OpenAI GPT-4)
- 💳 Stripe integration with webhook
- 🔁 Smart session memory for cart state
- 🪄 Suggestive upsell logic (e.g., drinks with pizza)

---

## 🏁 Final Word
> “Gods need temples. HungerGod needs servers.”

Serve joy. One order at a time.
