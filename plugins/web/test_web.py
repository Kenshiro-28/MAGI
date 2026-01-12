import web

WEB_SEARCH = "Who was Sun Tzu?"
PDF_URL = "https://ia803407.us.archive.org/35/items/TheArtOfWarBySunTzu/ArtOfWar.pdf"
CODE_URL = "https://github.com/Kenshiro-28/MAGI/blob/main/agent.py"
MAX_URLS = 3


if __name__ == "__main__":
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

    # Code scraping test
    text = web.scrape(CODE_URL)
    print("\n\nCode scraping:\n\n" + text)


