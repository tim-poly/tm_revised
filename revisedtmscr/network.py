import requests
import time
import random
from requests.adapters import HTTPAdapter
from config import USER_AGENTS
from utils import log

SESSION = requests.Session()

adapter = HTTPAdapter(pool_connections=20, pool_maxsize=20)
SESSION.mount('http://', adapter)
SESSION.mount('https://', adapter)

_SESSION_UA = random.choice(USER_AGENTS)

_BASE_HEADERS = {
    # Keep one stable UA per run; rotating every request is unusually bot-like.
    "User-Agent": _SESSION_UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "sv-SE,sv;q=0.9,en-US;q=0.8,en;q=0.7",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

class RequestScheduler:

    def __init__(self):
        self.base_delay = 1.2
        self.max_delay = 30
        self.current_delay = 3

    def wait(self):
        sleep_time = random.uniform(self.current_delay, self.current_delay + 2)
        log(f"[WAIT] sleeping {round(sleep_time,2)}s")
        time.sleep(sleep_time)

    def success(self):
        self.current_delay = max(self.base_delay, self.current_delay * 0.9)

    def rate_limited(self):
        self.current_delay = min(self.max_delay, self.current_delay * 1.7)
        log(f"[RATE LIMIT] delay → {round(self.current_delay,2)}s")


scheduler = RequestScheduler()


def fetch_page(url, retries=5, return_status=False):

    for attempt in range(retries):

        scheduler.wait()

        try:
            headers = dict(_BASE_HEADERS)
            # Only send a referer when we are hitting the Swedish site.
            if url.startswith("https://www.thomann.se/"):
                headers["Referer"] = "https://www.thomann.se/"

            response = SESSION.get(
                url,
                headers=headers,
                timeout=15
            )

            if response.status_code == 404:
                print(f"404 page: {url}")
                return (None, 404) if return_status else None

            if response.status_code == 403:
                # Treat 403 as a hard block; backing off may help, but repeated retries tend to worsen it.
                log(f"[FORBIDDEN] 403 for {url}")
                scheduler.rate_limited()
                if attempt < retries - 1:
                    time.sleep(random.uniform(10, 25))
                    continue
                return (None, 403) if return_status else None

            if response.status_code == 429:
                scheduler.rate_limited()
                continue

            if response.status_code >= 500:
                scheduler.rate_limited()
                continue

            response.raise_for_status()

            scheduler.success()
            return (response.text, response.status_code) if return_status else response.text

        except requests.RequestException as e:

            wait = random.uniform(5, 15)
            print(f"Request failed: {e}")
            print(f"Retrying in {round(wait,1)} seconds...")
            time.sleep(wait)

        if attempt > 0 and attempt % 3 == 0:
            # If the site sets a bad cookie we may want to recover, but don't nuke cookies immediately.
            SESSION.cookies.clear()

    return (None, None) if return_status else None
