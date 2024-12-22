from random import uniform
import requests
import time
import csv
from datetime import date, timedelta
from bs4 import BeautifulSoup

# Get the current date
today = date.today()
week_from_now = today + timedelta(days=7)

# Extract day, month, and year
current_day = today.day
current_month = today.month
current_year = today.year

future_day = week_from_now.day
future_month = week_from_now.month
future_year = week_from_now.year
    
# initialize the list of discovered urls
# with the first page to visit
# start_url = f"https://visitseattle.org/?s=&frm=events&event_begin={current_month}%2F{current_day}%2F{current_year}&event_end={future_month}%2F{future_day}%2F{future_year}&partner_parent_cat="

start_url = "https://visitseattle.org/events/law-rocks/"
urls = { start_url }
visited = []
data = {}

# until all pages have been visited
while len(urls) != 0:

    # get the page to visit from the list
    current_url = urls.pop()
    print("Current URL: ", current_url, "\n")
    
    # crawling logic
    if current_url not in visited:
        response = requests.get(current_url)

        #avoid loops
        visited.append(current_url)

        # Add a random delay between 3 and 7 seconds
        time.sleep(uniform(3, 7))
        soup = BeautifulSoup(response.content, "html.parser")
            

        for link_element in soup.find_all('a', href=True):
            url = link_element['href']
            if ("https://visitseattle.org" in url) and ("frm=events" in url or "https://visitseattle.org/events/" in url):
                urls.add(url)
            
        if "frm=events" not in current_url:
            event = {}
            event["name"] = soup.select_one('.event-top .page-title').text
            event["date"] = soup.select('.event-top h4 span')[0].text
            event['location'] = soup.select('.event-top h4 span')[1].text
            event['category'] = list(map(lambda x: x.text, soup.select('.category')))
            event["description"] = soup.select('.container-event-detail p')[1].text
            event["website"] = soup.select('.container-event-detail .medium-6  li a')[-1].text

        print(event)

        break

        print("Visited: ", visited, "\n")
        print("Urls to visit: ", urls, "\n")

print("Done")