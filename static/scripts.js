const input    = document.getElementById('userInput');
const sendBtn  = document.getElementById('sendBtn');
const messages = document.getElementById('chatMessages');

input.addEventListener('keydown', function(e) {
  if (e.key === 'Enter') sendMessage();
});

function scrollToBottom() {
  messages.scrollTop = messages.scrollHeight;
}

function addMessage(text, sender) {
  const row = document.createElement('div');
  row.className = 'message ' + sender;

  const avatar = document.createElement('div');
  avatar.className = 'avatar';
  avatar.textContent = sender === 'bot' ? '🌸' : '👤';

  const bubble = document.createElement('div');
  bubble.className = 'bubble';
  bubble.textContent = text;

  row.appendChild(avatar);
  row.appendChild(bubble);
  messages.appendChild(row);
  scrollToBottom();
}

function showTyping() {
  const row = document.createElement('div');
  row.className = 'message bot typing';
  row.id = 'typingIndicator';

  const avatar = document.createElement('div');
  avatar.className = 'avatar';
  avatar.textContent = '🌸';

  const bubble = document.createElement('div');
  bubble.className = 'bubble';
  bubble.innerHTML = '<div class="dot"></div><div class="dot"></div><div class="dot"></div>';

  row.appendChild(avatar);
  row.appendChild(bubble);
  messages.appendChild(row);
  scrollToBottom();
}

function removeTyping() {
  const el = document.getElementById('typingIndicator');
  if (el) el.remove();
}

function sendMessage() {
  const text = input.value.trim();
  if (!text) return;

  addMessage(text, 'user');
  input.value = '';
  sendBtn.disabled = true;

  showTyping();

  fetch('/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message: text })
  })
  .then(response => response.json())
  .then(data => {
    removeTyping();
    addMessage(data.reply, 'bot');
    sendBtn.disabled = false;
    input.focus();
  })
  .catch(error => {
    removeTyping();
    addMessage('Sorry, something went wrong. Please try again.', 'bot');
    sendBtn.disabled = false;
    input.focus();
  });
}