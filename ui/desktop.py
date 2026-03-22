"""
PyQt5 Desktop GUI for JARVIS.
"""

from __future__ import annotations

import logging
import threading
from typing import Optional

logger = logging.getLogger(__name__)

try:
    from PyQt5.QtCore import Qt, QThread, pyqtSignal, pyqtSlot
    from PyQt5.QtGui import QFont, QColor, QPalette
    from PyQt5.QtWidgets import (
        QApplication,
        QFrame,
        QHBoxLayout,
        QLabel,
        QMainWindow,
        QPushButton,
        QScrollArea,
        QSizePolicy,
        QTextEdit,
        QVBoxLayout,
        QWidget,
    )

    _PYQT5_AVAILABLE = True
except ImportError:
    _PYQT5_AVAILABLE = False
    logger.error("PyQt5 not installed. The desktop GUI cannot start.")


if _PYQT5_AVAILABLE:

    class _WorkerThread(QThread):
        """Background thread that calls JARVIS and emits the result."""

        response_ready = pyqtSignal(str, str)  # (speaker, message)
        error_occurred = pyqtSignal(str)

        def __init__(self, jarvis, user_text: str, use_voice: bool = False):
            super().__init__()
            self._jarvis = jarvis
            self._user_text = user_text
            self._use_voice = use_voice

        def run(self):
            try:
                if self._use_voice:
                    text = self._jarvis.listen()
                    if text:
                        self.response_ready.emit("You", text)
                        response = self._jarvis.respond(text)
                        self.response_ready.emit("JARVIS", response)
                    else:
                        self.error_occurred.emit("I couldn't hear anything. Please try again.")
                else:
                    response = self._jarvis.respond(self._user_text)
                    self.response_ready.emit("JARVIS", response)
            except Exception as exc:
                logger.error("Worker thread error: %s", exc)
                self.error_occurred.emit(f"An error occurred: {exc}")

    class JarvisDesktopApp(QMainWindow):
        """Main JARVIS desktop window."""

        def __init__(self):
            super().__init__()
            from core.jarvis import Jarvis
            from config.settings import settings

            self._settings = settings
            self._jarvis = Jarvis(speech_enabled=True)
            self._worker: Optional[_WorkerThread] = None

            self._setup_ui()
            self._apply_style()
            self._add_message("JARVIS", f"Hello! I'm {settings.JARVIS_NAME}. How can I help you?")

        # ---------------------------------------------------------------
        # UI setup
        # ---------------------------------------------------------------

        def _setup_ui(self):
            self.setWindowTitle(f"{self._settings.JARVIS_NAME} AI Assistant")
            self.setMinimumSize(700, 500)
            self.resize(800, 600)

            central = QWidget()
            self.setCentralWidget(central)
            main_layout = QVBoxLayout(central)
            main_layout.setContentsMargins(16, 16, 16, 16)
            main_layout.setSpacing(12)

            # Title bar
            title_label = QLabel(f"🤖 {self._settings.JARVIS_NAME} AI Assistant")
            title_font = QFont("Arial", 16, QFont.Bold)
            title_label.setFont(title_font)
            title_label.setAlignment(Qt.AlignCenter)
            main_layout.addWidget(title_label)

            # Chat display area
            self._chat_area = QTextEdit()
            self._chat_area.setReadOnly(True)
            self._chat_area.setFont(QFont("Consolas", 11))
            main_layout.addWidget(self._chat_area, stretch=1)

            # Status label
            self._status_label = QLabel("Ready")
            self._status_label.setAlignment(Qt.AlignCenter)
            main_layout.addWidget(self._status_label)

            # Input row
            input_row = QHBoxLayout()
            self._input_box = QTextEdit()
            self._input_box.setMaximumHeight(70)
            self._input_box.setPlaceholderText("Type your message here…")
            self._input_box.setFont(QFont("Arial", 11))
            input_row.addWidget(self._input_box, stretch=1)

            btn_layout = QVBoxLayout()
            self._send_btn = QPushButton("Send")
            self._send_btn.clicked.connect(self._on_send)
            self._send_btn.setFixedSize(80, 30)

            self._voice_btn = QPushButton("🎤 Voice")
            self._voice_btn.clicked.connect(self._on_voice)
            self._voice_btn.setFixedSize(80, 30)

            btn_layout.addWidget(self._send_btn)
            btn_layout.addWidget(self._voice_btn)
            input_row.addLayout(btn_layout)
            main_layout.addLayout(input_row)

        def _apply_style(self):
            self.setStyleSheet(
                """
                QMainWindow { background-color: #1e1e2e; }
                QWidget { background-color: #1e1e2e; color: #cdd6f4; }
                QTextEdit {
                    background-color: #181825;
                    color: #cdd6f4;
                    border: 1px solid #45475a;
                    border-radius: 6px;
                    padding: 6px;
                }
                QPushButton {
                    background-color: #89b4fa;
                    color: #1e1e2e;
                    border: none;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover { background-color: #74c7ec; }
                QPushButton:disabled { background-color: #45475a; color: #6c7086; }
                QLabel { color: #cdd6f4; }
                """
            )

        # ---------------------------------------------------------------
        # Helpers
        # ---------------------------------------------------------------

        def _add_message(self, speaker: str, message: str):
            color = "#89b4fa" if speaker == "JARVIS" else "#a6e3a1"
            self._chat_area.append(
                f'<span style="color:{color};font-weight:bold;">{speaker}:</span> '
                f'<span style="color:#cdd6f4;">{message}</span><br>'
            )

        def _set_busy(self, busy: bool):
            self._send_btn.setEnabled(not busy)
            self._voice_btn.setEnabled(not busy)
            self._input_box.setEnabled(not busy)
            self._status_label.setText("Processing…" if busy else "Ready")

        # ---------------------------------------------------------------
        # Event handlers
        # ---------------------------------------------------------------

        def _on_send(self):
            text = self._input_box.toPlainText().strip()
            if not text:
                return
            self._input_box.clear()
            self._add_message("You", text)
            self._set_busy(True)

            self._worker = _WorkerThread(self._jarvis, text, use_voice=False)
            self._worker.response_ready.connect(self._on_response)
            self._worker.error_occurred.connect(self._on_error)
            self._worker.finished.connect(lambda: self._set_busy(False))
            self._worker.start()

        def _on_voice(self):
            self._set_busy(True)
            self._status_label.setText("Listening… speak now")

            self._worker = _WorkerThread(self._jarvis, "", use_voice=True)
            self._worker.response_ready.connect(self._on_response)
            self._worker.error_occurred.connect(self._on_error)
            self._worker.finished.connect(lambda: self._set_busy(False))
            self._worker.start()

        @pyqtSlot(str, str)
        def _on_response(self, speaker: str, message: str):
            self._add_message(speaker, message)

        @pyqtSlot(str)
        def _on_error(self, message: str):
            self._add_message("JARVIS", f"⚠ {message}")

        def closeEvent(self, event):
            logger.info("Desktop GUI closing.")
            event.accept()

else:
    # Stub so imports don't fail when PyQt5 is missing
    class JarvisDesktopApp:  # type: ignore
        def __init__(self):
            raise RuntimeError("PyQt5 is not installed. Cannot launch desktop GUI.")
