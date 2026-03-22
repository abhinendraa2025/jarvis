"""
Flask web interface for JARVIS.
"""

from __future__ import annotations

import logging

from flask import Flask, jsonify, render_template_string, request

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Inline HTML template (no separate templates directory needed)
# ---------------------------------------------------------------------------

_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>JARVIS AI Assistant</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      background: #1e1e2e;
      color: #cdd6f4;
      display: flex;
      flex-direction: column;
      height: 100vh;
    }
    header {
      background: #181825;
      padding: 16px 24px;
      border-bottom: 1px solid #45475a;
      text-align: center;
      font-size: 1.4rem;
      font-weight: bold;
      color: #89b4fa;
    }
    #chat-box {
      flex: 1;
      overflow-y: auto;
      padding: 20px 24px;
      display: flex;
      flex-direction: column;
      gap: 10px;
    }
    .msg { max-width: 75%; padding: 10px 14px; border-radius: 12px; line-height: 1.5; white-space: pre-wrap; }
    .msg.user  { align-self: flex-end; background: #313244; color: #a6e3a1; }
    .msg.jarvis { align-self: flex-start; background: #45475a; color: #cdd6f4; }
    .msg .label { font-weight: bold; font-size: 0.8rem; margin-bottom: 4px; }
    .msg.user  .label { color: #a6e3a1; }
    .msg.jarvis .label { color: #89b4fa; }
    #input-area {
      display: flex;
      gap: 10px;
      padding: 16px 24px;
      background: #181825;
      border-top: 1px solid #45475a;
    }
    #user-input {
      flex: 1;
      padding: 10px 14px;
      border-radius: 8px;
      border: 1px solid #45475a;
      background: #1e1e2e;
      color: #cdd6f4;
      font-size: 1rem;
      outline: none;
    }
    #user-input:focus { border-color: #89b4fa; }
    button {
      padding: 10px 20px;
      border: none;
      border-radius: 8px;
      background: #89b4fa;
      color: #1e1e2e;
      font-weight: bold;
      cursor: pointer;
      font-size: 0.95rem;
    }
    button:hover { background: #74c7ec; }
    button:disabled { background: #45475a; color: #6c7086; cursor: not-allowed; }
    #status { text-align: center; padding: 6px; font-size: 0.8rem; color: #6c7086; }
  </style>
</head>
<body>
  <header>🤖 JARVIS AI Assistant</header>
  <div id="chat-box"></div>
  <div id="status"></div>
  <div id="input-area">
    <input id="user-input" type="text" placeholder="Type your message and press Enter…" autofocus />
    <button id="send-btn" onclick="sendMessage()">Send</button>
    <button id="history-btn" onclick="loadHistory()">History</button>
  </div>
  <script>
    const chatBox = document.getElementById('chat-box');
    const input   = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const status  = document.getElementById('status');

    input.addEventListener('keydown', e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); } });

    function addMessage(speaker, text) {
      const cls = speaker.toLowerCase() === 'you' ? 'user' : 'jarvis';
      const div = document.createElement('div');
      div.className = 'msg ' + cls;
      div.innerHTML = '<div class="label">' + speaker + '</div>' + escapeHtml(text);
      chatBox.appendChild(div);
      chatBox.scrollTop = chatBox.scrollHeight;
    }

    function escapeHtml(text) {
      return text.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
    }

    function setStatus(msg) { status.textContent = msg; }

    async function sendMessage() {
      const text = input.value.trim();
      if (!text) return;
      input.value = '';
      addMessage('You', text);
      sendBtn.disabled = true;
      setStatus('JARVIS is thinking…');
      try {
        const res = await fetch('/api/chat', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({message: text})
        });
        const data = await res.json();
        addMessage('JARVIS', data.response || data.error || 'No response.');
      } catch(err) {
        addMessage('JARVIS', 'Error: ' + err.message);
      } finally {
        sendBtn.disabled = false;
        setStatus('');
      }
    }

    async function loadHistory() {
      setStatus('Loading history…');
      try {
        const res = await fetch('/api/history');
        const data = await res.json();
        chatBox.innerHTML = '';
        (data.history || []).forEach(item => addMessage(item.speaker, item.message));
        setStatus('History loaded.');
      } catch(err) {
        setStatus('Failed to load history: ' + err.message);
      }
    }

    // Load a greeting on page load
    window.addEventListener('DOMContentLoaded', async () => {
      try {
        const res = await fetch('/api/chat', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({message: 'hello'})
        });
        const data = await res.json();
        addMessage('JARVIS', data.response || 'Hello!');
      } catch(_) {}
    });
  </script>
</body>
</html>
"""


def create_app() -> Flask:
    """Create and configure the Flask application."""
    from config.settings import settings
    from core.jarvis import Jarvis

    app = Flask(__name__)
    app.secret_key = settings.SECRET_KEY

    # Singleton JARVIS instance (speech disabled for web mode)
    jarvis = Jarvis(speech_enabled=False)

    @app.route("/")
    def index():
        return render_template_string(_HTML)

    @app.route("/api/chat", methods=["POST"])
    def chat():
        data = request.get_json(silent=True) or {}
        message = data.get("message", "").strip()
        if not message:
            return jsonify({"error": "No message provided"}), 400
        response = jarvis.process(message)
        return jsonify({"response": response})

    @app.route("/api/history", methods=["GET"])
    def history():
        limit = min(int(request.args.get("limit", 50)), 200)
        entries = jarvis.get_history(limit=limit)
        return jsonify({"history": entries})

    @app.route("/api/status", methods=["GET"])
    def status():
        return jsonify(
            {
                "name": settings.JARVIS_NAME,
                "version": settings.JARVIS_VERSION,
                "status": "running",
            }
        )

    logger.info("Flask app created.")
    return app
