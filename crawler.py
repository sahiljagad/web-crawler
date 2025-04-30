import requests
import re
import time
from datetime import date, timedelta
from random import uniform
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Event
from urllib.parse import urlparse

BASE_URL = "https://dothebay.com"
HEADERS = {}  # You can add headers later if needed (e.g., User-Agent with contact info for politeness)

# Compile regex once
EVENT_REGEX = re.compile(r"((\/events\/)|(\/\?page=\d))((\d{4})\/(\d{0,2})\/(\d{0,2}))")

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

def extract_event_data(soup: BeautifulSoup) -> dict:
    try:
        return {
            "name": soup.select_one('.ds-event-title-text').text.strip(),
            "location": soup.select_one('.ds-venue-name').text.strip(),
            "date": soup.select_one('.ds-event-date').text.strip(),
            "price": soup.find(itemprop='price').text.strip(),
            "time": soup.select_one('.ds-event-time').text.strip(),
            "website": soup.find('a', {'class': 'ds-buy-tix'}).get("href")
        }
    except Exception as e:
        print("Event data incomplete or failed to parse:", e)
        return None

def extract_date_from_url(url: str):
    try:
        parts = urlparse(url).path.strip("/").split("/")
        if len(parts) >= 4 and parts[-3].isdigit():
            year, month, day = int(parts[-3]), int(parts[-2]), int(parts[-1])
            return date(year, month, day)
    except:
        pass
    return None

def crawl():
    today = date.today()
    end_date = today + timedelta(days=7)
    urls_to_visit = populate_start_urls(today)
    visited_urls = set()
    new_events = []

    db: Session = SessionLocal()

    while urls_to_visit:
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
                        urls_to_visit.add(full_url)

        # Parse event details
        if 'page=' not in url and len(url) > 36:
            event_data = extract_event_data(soup)
            if event_data:
                event = Event(**event_data)
                new_events.append(event)

        time.sleep(uniform(2, 4))  # Respectful crawling

    # Bulk insert
    if new_events:
        db.bulk_save_objects(new_events)
        db.commit()

    db.close()
    print(f"Crawling complete. {len(new_events)} events saved.")

if __name__ == "__main__":
    crawl()
