"""Start the unified local GIS website and open it automatically."""
import threading
import time
import webbrowser
import uvicorn

def open_site():
    time.sleep(3)
    webbrowser.open("http://127.0.0.1:8000/")

if __name__ == "__main__":
    threading.Thread(target=open_site, daemon=True).start()
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=False)
