import requests
import re
import os
import time
from datetime import date, datetime, timedelta
from random import uniform
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

BASE_URL = "https://dothebay.com"
HEADERS = {"User-Agent": "BayAreaEventsCrawler/1.0 (github.com/sahiljagad/web-crawler)"}

# Compile regex once
EVENT_REGEX = re.compile(r"((\/events\/)|(\/\?page=\d))((\d{4})\/(\d{0,2})\/(\d{0,2}))(\/?)(.*)")


def populate_start_urls(today: date) -> set:
    urls = set()
    for i in range(1, 8):
        day = today + timedelta(days=i)
        urls.add(f"{BASE_URL}/events/{day.year}/{day.month}/{day.day}")
    return urls


def get_soup(url: str) -> BeautifulSoup:
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return BeautifulSoup(response.content, "html.parser")
    except Exception as e:
        print(f"Request failed for {url}: {e}")
        return None


def parse_event_date(date_text: str) -> str:
    """Parse date text like 'Saturday, April 12, 2025' into 'YYYY-MM-DD' format."""
    formats = ["%A, %B %d, %Y", "%B %d, %Y", "%m/%d/%Y"]
    for fmt in formats:
        try:
            return datetime.strptime(date_text, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def extract_event_data(soup: BeautifulSoup) -> dict:
    try:
        date_text = soup.select_one('.ds-event-date').text.strip()
        event_date = parse_event_date(date_text)

        return {
            "name": soup.select_one('.ds-event-title-text').text.strip(),
            "location": soup.select_one('.ds-venue-name').text.strip(),
            "event_date": event_date,
            "price": soup.find(itemprop='price').text.strip(),
            "start_time": soup.select_one('.ds-event-time').text.strip(),
            "website": soup.find('a', {'class': 'ds-buy-tix'}).get("href")
        }
    except Exception as e:
        print("Event data incomplete or failed to parse:", e)
        return None


def extract_date_from_url(url: str):
    try:
        parts = url.split("/")
        # URL like https://dothebay.com/events/2025/4/12/event-slug
        # parts: ['https:', '', 'dothebay.com', 'events', '2025', '4', '12', ...]
        if len(parts) >= 7:
            year, month, day = int(parts[4]), int(parts[5]), int(parts[6])
            return date(year, month, day)
    except (ValueError, IndexError):
        pass
    return None


def is_event_page(url: str) -> bool:
    """Check if URL is an individual event page (has a slug after the date segments)."""
    parts = url.rstrip("/").split("/")
    # Event pages: .../events/YYYY/M/D/event-slug (8+ parts)
    # Listing pages: .../events/YYYY/M/D (7 parts) or contain ?page=
    return "page=" not in url and len(parts) >= 8


def notify_new_events(events: list):
    topic = os.getenv("NTFY_TOPIC")
    if not topic or not events:
        return
    count = len(events)
    sample = events[0]["name"]
    message = f"{count} Bay Area events found this week!\nExample: {sample}"
    try:
        requests.post(
            f"https://ntfy.sh/{topic}",
            data=message,
            headers={"Title": "New Bay Area Events", "Priority": "default"}
        )
        print(f"Notification sent to ntfy.sh/{topic}")
    except Exception as e:
        print(f"ntfy notification failed: {e}")


def crawl(max_pages=None):
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
    if not supabase_url or not supabase_key:
        print("Error: SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")
        return

    supabase = create_client(supabase_url, supabase_key)

    today = date.today()
    end_date = today + timedelta(days=7)
    urls_to_visit = populate_start_urls(today)
    visited_urls = set()
    new_events = []

    while urls_to_visit:
        if max_pages and len(visited_urls) >= max_pages:
            print(f"Reached max pages limit ({max_pages}), stopping.")
            break

        url = urls_to_visit.pop()
        if url in visited_urls:
            continue

        print(f"Visiting: {url}")
        visited_urls.add(url)
        soup = get_soup(url)
        if not soup:
            continue

        # Find and enqueue new URLs
        for link in soup.find_all('a', href=True):
            href = link['href']
            if EVENT_REGEX.match(href):
                full_url = BASE_URL + href if href.startswith("/") else href
                event_date = extract_date_from_url(full_url)

                if full_url not in visited_urls and event_date:
                    if today <= event_date <= end_date:
                        print(f"Enqueuing URL: {full_url}")
                        urls_to_visit.add(full_url)

        # Parse event details from individual event pages
        if is_event_page(url):
            event_data = extract_event_data(soup)
            if event_data:
                new_events.append(event_data)

        time.sleep(uniform(2, 4))  # Respectful crawling

    # Upsert to Supabase (deduplicates on name + event_date + location)
    if new_events:
        result = supabase.table("events").upsert(
            new_events,
            on_conflict="name,event_date,location"
        ).execute()
        print(f"Upserted {len(new_events)} events.")
        notify_new_events(new_events)
    else:
        print("No events found.")

    print("Crawling complete.")


if __name__ == "__main__":
    crawl()
