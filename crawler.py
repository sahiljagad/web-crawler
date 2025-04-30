from bs4 import BeautifulSoup
import requests
import time
import re
from datetime import date, timedelta
from random import uniform
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import Event

# Function to create starting URLs
def populate_url_start_set(today, urls):
    for i in range(1, 8):
        day = today + timedelta(days=i)
        urls.add(f"https://dothebay.com/events/{day.year}/{day.month}/{day.day}")

# Get the current date
today = date.today()
week_from_now = today + timedelta(days=7)

# Regex for event URLs
regxp = re.compile(r"((\/events\/)|(\/\?page=\d))((\d{4})\/(\d{0,2})\/(\d{0,2}))")

# Initialize the set of URLs to visit
urls = set()
populate_url_start_set(today, urls)
visited = []

# Database session
db = SessionLocal()

# Web scraping loop
while urls:
    current_url = urls.pop()
    print("Crawling:", current_url)
    
    if current_url not in visited:
        response = requests.get(current_url)
        visited.append(current_url)
        time.sleep(uniform(3, 7))  # Random delay to avoid bans
        soup = BeautifulSoup(response.content, "html.parser")

        # Extract new URLs
        for link in soup.find_all('a', href=True):
            url = link['href']
            if regxp.match(url):
                full_url = "https://dothebay.com" + url
                urls.add(full_url)

        # Extract event data
        if 'page=' not in current_url and len(current_url) > 36:
            try:
                event = Event(
                    name=soup.select_one('.ds-event-title-text').text.strip(),
                    location=soup.select_one('.ds-venue-name').text.strip(),
                    date=soup.select_one('.ds-event-date').text.strip(),
                    price=soup.find(itemprop='price').text.strip(),
                    time=soup.select_one('.ds-event-time').text.strip(),
                    website=soup.find('a', {'class': 'ds-buy-tix'}).get("href"),
                )
                db.add(event)
                db.commit()
            except Exception as e:
                print("Error parsing event:", e)

db.close()
print("Crawling complete.")
