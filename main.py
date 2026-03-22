"""
JARVIS AI Assistant - Main Entry Point

Usage:
    python main.py --desktop    # Launch desktop GUI
    python main.py --web        # Launch web interface
    python main.py --both       # Launch both interfaces
    python main.py              # Default: launch desktop GUI
"""

import argparse
import sys
import threading
import logging

from utils.logger import setup_logger
from config.settings import settings

logger = setup_logger(__name__)


def run_desktop():
    """Launch the PyQt5 desktop GUI."""
    try:
        from PyQt5.QtWidgets import QApplication
        from ui.desktop import JarvisDesktopApp

        app = QApplication(sys.argv)
        app.setApplicationName(settings.JARVIS_NAME)
        window = JarvisDesktopApp()
        window.show()
        logger.info("Desktop GUI started")
        return app.exec_()
    except ImportError as e:
        logger.error("PyQt5 is not installed. Run: pip install PyQt5  (%s)", e)
        print("Error: PyQt5 is required for the desktop interface.")
        print("Install it with: pip install PyQt5")
        return 1
    except Exception as e:
        logger.error("Failed to start desktop GUI: %s", e)
        return 1


def run_web():
    """Launch the Flask web interface."""
    try:
        from ui.web import create_app

        flask_app = create_app()
        logger.info(
            "Web interface starting at http://%s:%s",
            settings.FLASK_HOST,
            settings.FLASK_PORT,
        )
        flask_app.run(
            host=settings.FLASK_HOST,
            port=settings.FLASK_PORT,
            debug=settings.FLASK_DEBUG,
            use_reloader=False,
        )
    except Exception as e:
        logger.error("Failed to start web interface: %s", e)


def run_both():
    """Launch both desktop GUI and web interface concurrently."""
    web_thread = threading.Thread(target=run_web, daemon=True)
    web_thread.start()
    logger.info("Web interface launched in background thread")
    return run_desktop()


def parse_args():
    parser = argparse.ArgumentParser(
        description="JARVIS AI Assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--desktop", action="store_true", help="Launch desktop GUI (default)")
    mode.add_argument("--web", action="store_true", help="Launch web interface")
    mode.add_argument("--both", action="store_true", help="Launch both interfaces")
    return parser.parse_args()


def main():
    args = parse_args()

    logger.info(
        "Starting %s v%s", settings.JARVIS_NAME, settings.JARVIS_VERSION
    )

    if args.web:
        run_web()
    elif args.both:
        sys.exit(run_both())
    else:
        # --desktop is the default
        sys.exit(run_desktop())


if __name__ == "__main__":
    main()
