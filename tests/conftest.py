import functools
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.selenium_manager import SeleniumManager
from selenium.webdriver.chrome.options import Options


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DIST_DIR = PROJECT_ROOT / "dist"
SELENIUM_CACHE_DIR = PROJECT_ROOT / ".selenium"


def _pick_free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        sock.listen(1)
        return sock.getsockname()[1]


def _wait_until_server_is_ready(url: str, timeout: float = 10.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url) as response:
                if response.status == 200:
                    return
        except Exception:
            time.sleep(0.2)
    time.sleep(0.5)


def _find_chrome_binary() -> str | None:
    if chrome_binary := os.getenv("CHROME_BINARY"):
        return chrome_binary

    candidates = [
        Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
        Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
        Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
        Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    ]

    for candidate in candidates:
        if candidate.exists():
            return str(candidate)

    return None


def _resolve_chrome_driver(chrome_binary: str | None) -> tuple[str, str | None]:
    SELENIUM_CACHE_DIR.mkdir(exist_ok=True)

    cached_drivers = sorted(SELENIUM_CACHE_DIR.rglob("chromedriver*"))
    cached_driver_files = [path for path in cached_drivers if path.is_file() and path.name.startswith("chromedriver")]
    if cached_driver_files:
        return str(cached_driver_files[-1]), chrome_binary

    manager_binary = SeleniumManager()._get_binary()
    command = [
        str(manager_binary),
        "--browser",
        "chrome",
        "--language-binding",
        "python",
        "--output",
        "json",
        "--cache-path",
        str(SELENIUM_CACHE_DIR),
    ]
    if chrome_binary:
        command.extend(["--browser-path", chrome_binary])

    completed = subprocess.run(command, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
    if completed.returncode != 0:
        raise RuntimeError(
            "Selenium Manager failed to resolve Chrome driver.\n"
            f"STDOUT: {completed.stdout}\nSTDERR: {completed.stderr}"
        )

    result = json.loads(completed.stdout)["result"]
    return result["driver_path"], result.get("browser_path")


@pytest.fixture(scope="session")
def app_url() -> str:
    port = _pick_free_port()
    handler = functools.partial(SimpleHTTPRequestHandler, directory=str(DIST_DIR))
    server = ThreadingHTTPServer(("127.0.0.1", port), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    url = f"http://127.0.0.1:{port}/"

    try:
        thread.start()
        _wait_until_server_is_ready(url)
        yield url
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


@pytest.fixture
def driver():
    options = Options()
    chrome_binary = _find_chrome_binary()
    if chrome_binary:
        options.binary_location = chrome_binary

    profile_dir = tempfile.mkdtemp(prefix="chrome-profile-")

    options.add_argument("--headless=new")
    options.add_argument("--window-size=1600,1200")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--remote-debugging-port=0")
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument(f"--user-data-dir={profile_dir}")
    options.add_argument("--lang=ru-RU")

    driver_path, resolved_browser_path = _resolve_chrome_driver(chrome_binary)
    if not options.binary_location and resolved_browser_path:
        options.binary_location = resolved_browser_path

    browser = webdriver.Chrome(service=Service(executable_path=driver_path), options=options)
    browser.implicitly_wait(2)

    try:
        yield browser
    finally:
        try:
            browser.quit()
        except Exception:
            pass
        shutil.rmtree(profile_dir, ignore_errors=True)
