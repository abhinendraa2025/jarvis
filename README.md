# JARVIS AI Assistant

A complete, production-ready AI assistant with speech recognition, NLP, a PyQt5 desktop GUI, and a Flask web interface.

## Features

- 🎤 **Speech Recognition** – voice input via SpeechRecognition + Google Speech API
- 🔊 **Text-to-Speech** – voice output via pyttsx3
- 🖥️ **Desktop GUI** – PyQt5 dark-mode chat interface
- 🌐 **Web Interface** – Flask REST API + browser chat UI
- 🧠 **NLP** – intent detection and keyword extraction with NLTK
- 🗄️ **Database** – SQLite conversation history
- ⚙️ **Configuration** – `.env`-based settings

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure (optional)

Edit `.env` to set your preferences (speech rate, Flask port, etc.).

### 3. Run

```bash
# Desktop GUI (default)
python main.py --desktop

# Web interface  (open http://127.0.0.1:5000 in your browser)
python main.py --web

# Both simultaneously
python main.py --both
```

## Project Structure

```
jarvis/
├── main.py              # Entry point
├── requirements.txt     # Dependencies
├── .env                 # Configuration
├── config/
│   └── settings.py      # App settings
├── core/
│   ├── jarvis.py        # Core JARVIS class
│   ├── speech.py        # Speech I/O
│   └── nlp.py           # NLP processing
├── modules/
│   ├── web_search.py    # DuckDuckGo search
│   ├── calculator.py    # Safe math evaluator
│   └── system.py        # System info
├── ui/
│   ├── desktop.py       # PyQt5 GUI
│   └── web.py           # Flask web app
└── utils/
    ├── logger.py        # Rotating file logger
    └── helpers.py       # Utility functions
```

## Supported Commands

| What you say | What JARVIS does |
|---|---|
| "Hello" / "Hi" | Greeting with time-aware message |
| "What time is it?" | Current time |
| "What's today's date?" | Current date |
| "Calculate 2 + 2" | Safe math evaluation |
| "Search for Python tutorials" | DuckDuckGo instant answer |
| "System info" | CPU / memory / disk usage |
| "Tell me a joke" | Random joke |
| "Help" | List of capabilities |
| "Goodbye" / "Exit" | Farewell |
