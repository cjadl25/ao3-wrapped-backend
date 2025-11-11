# scraper_live.py
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup
from collections import Counter
import re

def extract_number(text):
    return int(re.sub(r"[^\d]", "", text)) if text else 0

def scrape_ao3_with_progress(username, password, progress_callback=None):
    """
    Scrape AO3 reading history with progress callback.
    Returns stats dictionary.
    """
    fandom_counter = Counter()
    ship_counter = Counter()
    books_counter = Counter()
    rating_counter = Counter()
    total_words_counter = 0
    books_set = set()

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
            page = browser.new_page()

            # Login
            page.goto("https://archiveofourown.org/users/login")
            page.fill('form#new_user input[name="user[login]"]', username)
            page.fill('form#new_user input[name="user[password]"]', password)
            page.click('form#new_user input[type="submit"]')

            # Wait for either dashboard or error
            try:
                page.wait_for_selector("div.user.about", timeout=5000)
            except PlaywrightTimeoutError:
                # Login failed
                browser.close()
                raise ValueError("Login failed. Check your username/password.")

            # Determine total pages
            page.goto(f"https://archiveofourown.org/users/{username}/readings")
            soup = BeautifulSoup(page.content(), "html.parser")
            pagination = soup.select("ol.pagination li a")
            total_pages = 1
            if pagination:
                page_numbers = [int(a.get_text(strip=True)) for a in pagination if a.get_text(strip=True).isdigit()]
                if page_numbers:
                    total_pages = max(page_numbers)

            page_number = 1

            while page_number <= total_pages:
                page.goto(f"https://archiveofourown.org/users/{username}/readings?page={page_number}")
                page.wait_for_selector("li.reading.work.blurb.group", timeout=5000)
                soup = BeautifulSoup(page.content(), "html.parser")
                works = soup.select("li.reading.work.blurb.group")
                if not works:
                    break

                for work in works:
                    title_tag = work.select_one("h4 a")
                    if not title_tag:
                        continue
                    title = title_tag.get_text(strip=True)

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
                    progress_percentage = int((page_number / total_pages) * 100)
                    progress_callback(progress_percentage)

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

    except Exception as e:
        raise e
