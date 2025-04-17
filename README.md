# HungerGod 🍕

**HungerGod** is a production-ready, pluggable ordering assistant designed for restaurants.
Built for WhatsApp and Web, it brings intelligent, conversation-based food ordering to life — starting with pizza, but scalable to groceries, chai, desserts, and more.

Powered by **Flask**, enhanced with **LLMs**, integrated with **Stripe**, and deployable in minutes with **Render**.

---

## ⚙️ Structure 

```
.
├── app_web.py         # Web-based chatbot UI using Flask
├── chatbot.html       # Web chat UI
├── chatbot.js         # Client-side interaction logic
├── utils.py           # Order saving / data helpers
├── pizza_menu.json    # Editable menu (supports categories & aliases)
├── orders.json        # File-based order logs
├── requirements.txt   # Project dependencies
├── style.css          # Custom web UI styling
├── README.md          # You're reading it
```

---

## 🚀 Local Setup

```bash
git clone https://github.com/Agentibus-ai/HungerGod
cd HungerGod/src
pip install -r ../requirements.txt
python app_web.py
```

## ☁️ Production Deployment: [Render](https://hungergod.onrender.com/) 


## 🧠 Features
- ✅ Web-based UI (chat + menu + cart)
- 🧾 Dynamic JSON-based menu
- 🧠 LLM-powered intent parsing (OpenAI GPT-4)
- 💳 Stripe integration with webhook
- 🔁 Smart session memory for cart state
- 🪄 Suggestive upsell logic (e.g., drinks with pizza)

---

## 📌 Next Up
- Add persistent DB (MongoDB, Firebase, PostgreSQL)
- Admin dashboard for order management
- WhatsApp Business API integration
- Razorpay / PayPal payment support
- Multilingual / voice ordering (Whisper)
- Real-time order tracking

---

## 🏁 Final Word
> “Gods need temples. HungerGod needs servers.”

Serve joy. One order at a time.
