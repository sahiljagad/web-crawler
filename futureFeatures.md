# Future Features

## Event Categories
Add a way to organize and filter events by type (e.g., music, sports, leisure, comedy, arts, food & drink). Options:
- Scrape category tags from dothebay.com if available
- Use keyword matching on event names/venues to auto-categorize
- Add a `category` column to the events table
- Add a category filter to the frontend

## Area / Region Filter
Filter events by Bay Area region (SF, East Bay, South Bay, Peninsula, etc.). Options:
- Check if dothebay.com uses subdomains (e.g., eastbay.dothebay.com) or URL paths for areas
- Crawl each area separately and tag events with a `region` column
- Add a region filter dropdown to the frontend
