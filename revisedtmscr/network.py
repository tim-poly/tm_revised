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


def fetch_page(url, retries=5):

    for attempt in range(retries):

        scheduler.wait()

        try:
            headers = {
                "User-Agent": random.choice(USER_AGENTS),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1"
            }

            response = SESSION.get(
                url,
                headers=headers,
                timeout=15
            )

            if response.status_code == 404:
                print(f"404 page: {url}")
                return None

            if response.status_code == 429:
                scheduler.rate_limited()
                continue

            if response.status_code >= 500:
                scheduler.rate_limited()
                continue

            response.raise_for_status()

            scheduler.success()
            return response.text

        except requests.RequestException as e:

            wait = random.uniform(5, 15)
            print(f"Request failed: {e}")
            print(f"Retrying in {round(wait,1)} seconds...")
            time.sleep(wait)

    return None

