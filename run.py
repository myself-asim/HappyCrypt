from __future__ import annotations

import threading
import time
import webbrowser

import uvicorn

from backend.config import APP_NAME, HOST, PORT


def open_browser() -> None:
    # Give the server a moment to start before opening the UI.
    time.sleep(1.0)
    webbrowser.open(f"http://{HOST}:{PORT}")


def main() -> None:
    print(f"Starting {APP_NAME} on http://{HOST}:{PORT}")
    threading.Thread(target=open_browser, daemon=True).start()
    uvicorn.run("backend.main:app", host=HOST, port=PORT, reload=False, log_level="info")


if __name__ == "__main__":
    main()
