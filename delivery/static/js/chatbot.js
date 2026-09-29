document.addEventListener('DOMContentLoaded', () => {
  const bubble = document.getElementById('chat-bubble');
  const win = document.getElementById('chat-window');
  const closeBtn = document.getElementById('chat-close');
  const input = document.getElementById('chat-input');
  const sendBtn = document.getElementById('chat-send');
  const messages = document.getElementById('chat-messages');

  if (!bubble || !win) return;

  function toggleChat(open) {
    const isVisible = open !== undefined ? open : !win.classList.contains('open');
    win.classList.toggle('open', isVisible);
    bubble.setAttribute('aria-expanded', isVisible ? 'true' : 'false');
    if (isVisible && input) input.focus();
  }

  bubble.addEventListener('click', () => toggleChat());
  if (closeBtn) closeBtn.addEventListener('click', () => toggleChat(false));

  function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
  }

  function appendMsg(text, type = 'bot') {
    if (!messages) return;
    const div = document.createElement('div');
    div.className = `msg ${type}`;
    div.textContent = text;
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
  }

  async function handleSend() {
    if (!input) return;
    const val = input.value.trim();
    if (!val || input.disabled) return;

    appendMsg(val, 'user');
    input.value = '';
    input.disabled = true;
    if (sendBtn) sendBtn.disabled = true;

    try {
      const res = await fetch('/api/chat/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'X-CSRFToken': getCookie('csrftoken'),
        },
        body: `message=${encodeURIComponent(val)}`,
      });
      const data = await res.json();
      appendMsg(data.reply || 'حصلت مشكلة في الرد، جرّب تاني.', res.ok ? 'bot' : 'err');
    } catch {
      appendMsg('مفيش اتصال بالسيرفر — اتأكد إنه شغال.', 'err');
    } finally {
      input.disabled = false;
      if (sendBtn) sendBtn.disabled = false;
      input.focus();
    }
  }

  if (sendBtn) sendBtn.addEventListener('click', handleSend);
  if (input) {
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') handleSend();
    });
  }
});
