// chatbot.js for Pizzeria Da Mario – Upgraded AI Experience 🇮🇹

const chatBox = document.getElementById('chatBox');
const messageInput = document.getElementById('messageInput');
const sendButton = document.getElementById('sendButton');
const cartButton = document.getElementById('cartButton');
const cartSummary = document.getElementById('cartSummary');
const cartClose = document.getElementById('cartClose');
const cartItems = document.getElementById('cartItems');
const cartTotal = document.getElementById('cartTotal');
const cartCount = document.getElementById('cartCount');
const menuButton = document.getElementById('menuButton');
const checkoutButton = document.getElementById('checkoutButton');

let cart = [];

window.addEventListener('DOMContentLoaded', () => {
  setTimeout(() => {
    sendMessage('!welcome');
  }, 3000);
});

sendButton.addEventListener('click', () => {
  if (messageInput.value.trim()) sendMessage();
});

messageInput.addEventListener('keypress', e => {
  if (e.key === 'Enter' && messageInput.value.trim()) sendMessage();
});

cartButton.addEventListener('click', () => {
  cartSummary.classList.toggle('visible');
});

cartClose.addEventListener('click', () => {
  cartSummary.classList.remove('visible');
});

menuButton.addEventListener('click', () => sendMessage('menu'));
checkoutButton.addEventListener('click', () => sendMessage('checkout'));

function sendMessage(overrideMessage) {
  const message = overrideMessage || messageInput.value.trim();
  if (!message.length) return;

  if (message !== '!welcome') addMessage(message, 'user');
  messageInput.value = '';

  const typing = document.createElement('div');
  typing.className = 'typing-indicator';
  typing.textContent = 'Mario sta scrivendo...';
  chatBox.appendChild(typing);
  chatBox.scrollTop = chatBox.scrollHeight;

  fetch('/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message })
  })
    .then(res => res.json())
    .then(data => {
      chatBox.removeChild(typing);
      sendBotMessage(data.response);

      if (data.cart) {
        cart = data.cart;
        updateCartUI();
      }
    })
    .catch(err => {
      console.error(err);
      chatBox.removeChild(typing);
      sendBotMessage('Errore di connessione al server. Riprova più tardi.');
    });
}

function sendBotMessage(msg) {
  addMessage(msg, 'bot');
}

function addMessage(content, sender) {
  const msgEl = document.createElement('div');
  msgEl.className = `message ${sender}-message`;

  const contentEl = document.createElement('div');
  contentEl.className = 'message-content';
  contentEl.innerHTML = marked.parse(content);
  msgEl.appendChild(contentEl);

  const timeEl = document.createElement('div');
  timeEl.className = 'message-time';
  const now = new Date();
  timeEl.textContent = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;
  msgEl.appendChild(timeEl);

  chatBox.appendChild(msgEl);
  chatBox.scrollTop = chatBox.scrollHeight;
}

function updateCartUI() {
  let count = 0;
  const groupedItems = {};
  let total = 0;

  cart.forEach(item => {
    if (!groupedItems[item.name]) {
      groupedItems[item.name] = { count: 0, price: item.price };
    }
    groupedItems[item.name].count++;
    count++;
    total += item.price;
  });

  cartCount.textContent = count;

  if (count === 0) {
    cartButton.classList.add('empty');
    cartItems.innerHTML = '<div class="cart-item">Il tuo carrello è vuoto</div>';
    cartTotal.textContent = '€0.00';
    return;
  }

  cartButton.classList.remove('empty');
  cartItems.innerHTML = '';

  Object.entries(groupedItems).forEach(([name, { count, price }]) => {
    const itemEl = document.createElement('div');
    itemEl.className = 'cart-item';
    itemEl.innerHTML = `<span>${name} x${count}</span><span>€${(count * price).toFixed(2)}</span>`;
    cartItems.appendChild(itemEl);
  });

  cartTotal.textContent = `€${total.toFixed(2)}`;
}
