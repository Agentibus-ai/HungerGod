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
  // Disable send button until input has content
  sendButton.disabled = true;
  messageInput.addEventListener('input', () => {
    sendButton.disabled = !messageInput.value.trim();
  });
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

  let userMsgEl;
  if (message !== '!welcome') {
    userMsgEl = addMessage(message, 'user');
  }
  messageInput.value = '';

  // Send request and manage tick statuses and typing simulation
  fetch('/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message })
  })
    .then(res => {
      // Delivered: double gray ticks
      if (userMsgEl) updateStatus(userMsgEl, 'delivered');
      return res.json();
    })
    .then(data => {
      // Read: double blue ticks
      if (userMsgEl) updateStatus(userMsgEl, 'read');
      // Show typing indicator after read ticks
      const typing = document.createElement('div');
      typing.className = 'typing-indicator';
      typing.textContent = 'Mario sta scrivendo...';
      chatBox.appendChild(typing);
      typing.scrollIntoView({ behavior: 'smooth', block: 'end' });
      // Simulate typing delay
      setTimeout(() => {
        chatBox.removeChild(typing);
        sendBotMessage(data.response);
        if (data.cart) {
          cart = data.cart;
          updateCartUI();
        }
      }, 800);
    })
    .catch(err => {
      console.error(err);
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
  const hh = String(now.getHours()).padStart(2, '0');
  const mm = String(now.getMinutes()).padStart(2, '0');
  if (sender === 'user') {
    timeEl.innerHTML = `${hh}:${mm} <i class="fas fa-check single-tick"></i>`;
  } else {
    timeEl.textContent = `${hh}:${mm}`;
  }
  msgEl.appendChild(timeEl);

  chatBox.appendChild(msgEl);
  // Smooth scroll to the new message
  msgEl.scrollIntoView({ behavior: 'smooth', block: 'end' });
  // Refocus input
  messageInput.focus();
  return msgEl;
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
/**
 * Update tick status on user message:
 * 'delivered' => double gray ticks
 * 'read' => double blue ticks
 */
function updateStatus(msgEl, status) {
  const timeEl = msgEl.querySelector('.message-time');
  if (!timeEl) return;
  const tickEl = timeEl.querySelector('i');
  if (!tickEl) return;
  if (status === 'delivered') {
    tickEl.classList.remove('fa-check', 'single-tick');
    tickEl.classList.add('fa-check-double', 'double-tick');
  } else if (status === 'read') {
    tickEl.classList.remove('fa-check-double', 'double-tick');
    tickEl.classList.add('fa-check-double', 'read-tick');
  }
}
