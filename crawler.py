from random import uniform
import requests
import time
import re
from datetime import date, timedelta
from bs4 import BeautifulSoup
import pandas as pd

#function to create starting url list
def populate_url_start_set(today, urls):
    for i in range(1,8):
        day = today + timedelta(days=i)
        urls.add(f"https://dothebay.com/events/{day.year}/{day.month}/{day.day}")


# Get the current date
today = date.today()
week_from_now = today + timedelta(days=7)

# Extract day, month, and year into lists
today_list = [today.year, today.month, today.day]
future_list = [week_from_now.year, week_from_now.month, week_from_now.day]

#url regex
regxp = re.compile(r"((\/events\/)|(\/\?page=\d))((\d{4})\/(\d{0,2})\/(\d{0,2}))")
    
# initialize the list of discovered urls with the pages of events in next

urls = set()
populate_url_start_set(today, urls)
visited = []
data = []

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
            if regxp.match(url) is not None: 
                if 'page=' in url:
                    urls.add("https://dothebay.com" + url)
                else:
                    url_date = map(lambda x:int(x), url.split("/")[2:5])
                    if today_list <= list(url_date) <= future_list:
                        urls.add("https://dothebay.com" + url)
                
        if 'page=' not in current_url and len(current_url) > 36:
            try:
                event = {}
                event["Name"] = soup.select_one('.ds-event-title-text').text.strip() 
                event['Location'] = soup.select_one('.ds-ticket-info').text.strip() 
                event["Date"] = soup.select_one('.ds-event-date').text.strip() 
                event["Price"] = soup.find(itemprop='price').text.replace(" ", "").strip()
                event["Time"] = soup.select_one('.ds-event-time').text.strip()
                event['Location'] = soup.select_one('.ds-venue-name').text.replace("\u200b", "").strip()
                event["Website"] = soup.find('a', {'class': 'ds-buy-tix'}).get("href")
                data.append(event)
            except:
                pass

df = pd.DataFrame(data)
df.to_csv('bayAreaEvents.csv', index=False)

print("Done")