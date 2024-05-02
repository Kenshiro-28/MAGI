import web

WEB_SEARCH = "Who was Sun Tzu?"
PDF_URL = "https://ia803407.us.archive.org/35/items/TheArtOfWarBySunTzu/ArtOfWar.pdf"
MAX_URLS = 3

print("\nWeb search: " + WEB_SEARCH)

urls = web.search(WEB_SEARCH, MAX_URLS)

# Search & html scraping test
for url in urls:
    print("\n" + url)
    text = web.scrape(url)
    print("\n" + text)

# PDF scraping test
    text = web.scrape(PDF_URL)
    print("\n\nPDF scraping:\n\n" + text)


