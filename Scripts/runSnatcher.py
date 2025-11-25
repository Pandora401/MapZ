import os
import re
import requests
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from playwright.sync_api import sync_playwright

# Base tile URL prefix
BASE_PREFIX = "https://maps.izurvive.com/maps/ChernarusPlus-Top/1.26.0/tiles/"
OUTPUT_DIR = "../tiles"

_downloaded = set()
_tile_path_re = re.compile(re.escape(BASE_PREFIX) + r'([0-9A-Za-z_\-./]+\.webp)')

executor = ThreadPoolExecutor(max_workers=10)
lock = threading.Lock()
last_tile_time = time.time()

def download_tile(url: str):
    global last_tile_time
    with lock:
        if url in _downloaded:
            return
        _downloaded.add(url)
    rel_path_match = _tile_path_re.match(url)
    if not rel_path_match:
        return
    rel_path = rel_path_match.group(1)
    local_path = os.path.join(OUTPUT_DIR, rel_path)
    os.makedirs(os.path.dirname(local_path), exist_ok=True)

    try:
        resp = requests.get(url, stream=True, timeout=15)
        resp.raise_for_status()
        with open(local_path, "wb") as f:
            for chunk in resp.iter_content(8192):
                f.write(chunk)
        with lock:
            last_tile_time = time.time()
        print(f"Downloaded: {local_path}")
    except Exception as e:
        print(f"Failed {url}: {e}")

def schedule_download(url: str):
    executor.submit(download_tile, url)

def monitor_idle(timeout=30):
    """Alert if no new tile in timeout seconds."""
    while True:
        time.sleep(1)
        with lock:
            idle_time = time.time() - last_tile_time
        if idle_time > timeout:
            print(f"[!] No new tiles in the last {timeout} seconds.")
            last_tile_time = time.time()  # reset

def main():
    monitor_thread = threading.Thread(target=monitor_idle, daemon=True)
    monitor_thread.start()

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=["--start-fullscreen"],  # open full-screen
        )
        page = browser.new_page(viewport=None)  # None = use full screen

        # Capture tile requests
        page.on("request", lambda request: schedule_download(request.url)
                if request.url.startswith(BASE_PREFIX) else None)

        print("Opening DayZ map page in full-screen...")
        page.goto(
            "https://dayz.ginfo.gg/#c=27;-4;6",
            wait_until="networkidle",
            timeout=60000
        )

        print("Listening for tiles. Close the browser to stop...")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Exiting...")

        browser.close()
        executor.shutdown(wait=True)
        print("Done. All captured tiles have been downloaded.")

if __name__ == "__main__":
    main()
