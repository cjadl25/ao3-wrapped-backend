# scraper_live.py
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from collections import Counter
import time, re, os

def extract_number(text):
    """Extract integer from string, e.g. '1,234 words' -> 1234"""
    return int(re.sub(r"[^\d]", "", text)) if text else 0

def scrape_ao3_with_progress(username, password, progress_callback=None):
    fandom_counter = Counter()
    ship_counter = Counter()
    books_counter = Counter()
    rating_counter = Counter()
    total_words_counter = 0
    books_set = set()

    # Determine Chromium executable from environment variable
    chromium_base = os.environ.get("PLAYWRIGHT_BROWSERS_PATH", "")
    chrome_path = os.path.join(chromium_base, "chromium", "chrome-linux", "chrome")

    # Use headless Chromium
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=chrome_path)
        page = browser.new_page()

        # Login
        page.goto("https://archiveofourown.org/users/login")
        page.fill('form#new_user input[name="user[login]"]', username)
        page.fill('form#new_user input[name="user[password]"]', password)
        page.click('form#new_user input[type="submit"]')
        time.sleep(3)

        # Check for failed login
        if "Invalid username or password" in page.content():
            browser.close()
            raise ValueError("Incorrect username or password")

        page_number = 1
        total_pages_estimate = 5  # approximate, can adjust

        while True:
            page.goto(f"https://archiveofourown.org/users/{username}/readings?page={page_number}")
            time.sleep(1)
            soup = BeautifulSoup(page.content(), "html.parser")
            works = soup.select("li.reading.work.blurb.group")
            if not works:
                break

            for work in works:
                title_tag = work.select_one("h4 a")
                if not title_tag:
                    continue
                title = title_tag.get_text(strip=True)

                # Visits / rereads
                visit_tag = work.select_one("h4.viewed.heading")
                visits = 1
                if visit_tag:
                    match = re.search(r"Visited (\d+) times", visit_tag.get_text(strip=True))
                    if match:
                        visits = int(match.group(1))
                books_counter[title] += visits

                if title not in books_set:
                    books_set.add(title)
                    words_tag = work.select_one("dd.words")
                    total_words_counter += extract_number(words_tag.get_text()) if words_tag else 0

                    fandoms = [f.get_text(strip=True) for f in work.select("h5.fandoms a")]
                    fandom_counter.update(fandoms or ["Unknown"])

                    header_ul = work.select_one("div.header.module ul")
                    if header_ul:
                        lis = [li.get_text(strip=True) for li in header_ul.find_all("li")]
                        if lis:
                            rating_counter[lis[0]] += 1

                # Ships / pairings
                pairings = []
                for li in work.select("ul.tags.commas li.relationships"):
                    pairings.extend([p.strip() for p in li.get_text(strip=True).split(",")])
                for pairing in pairings:
                    ship_counter[pairing] += visits

            # Update progress
            if progress_callback:
                progress_callback(int((page_number / total_pages_estimate) * 100))

            page_number += 1

        browser.close()

    return {
        "total_books": len(books_set),
        "total_words": total_words_counter,
        "top_books": books_counter.most_common(5),
        "top_ships": ship_counter.most_common(5),
        "top_fandoms": fandom_counter.most_common(5),
        "top_ratings": rating_counter.most_common(5),
    }
